#!/usr/bin/env python3
# An example program for the REYAX RYLR998
# Written by Florian Lengyel, WM2D
#
# This software is released under an MIT license.
# See the accompanying LICENSE txt file.

# This code below was written to work with the REYAX RYLR998 LoRa module, using
# nothing more than five connections to the GPIO pins of a Rasperry 4 Model B Rev 1.5.
# No electronic components are needed other than five wires and ten female-female
# GPIO connectors. (Or connect the module directly to a GPIO head, etc., as you wish.)
#
# The GPIO connections are as follows:
#
# VDD to 3.3V physical pin 1 on the GPIO
# RST to GPIO 4, physical pin 7
# TXD to GPIO 15 RXD1 this is physical pin 10
# RXD to GPIO 14 TXD1 this is physical pin 8
# GND to GND physical pin 9.

# NOTE: GPIO pin 4, physical pin 7 is an OUTPUT pin with level one and pull=NONE.
# TO DO: Switch to the wiringpi library to program GPIO 4 alt5 with the pin pulled UP
# under normal operation, and pulled DOWN or at least 100ms to reset the module.
# The current configuration works, but can be improved. You could add a pull up
# resistor, but then it's five wires and a resistor. See the RYLR998 data sheet.
#
# AT commands follow the  "REYAX RYLR998 RYLR498 Lora AT COMMAND GUIDE"
# (c) 2021 REYAX TECHNOLOGY CO., LTD.
#
# Further instructions to be made available in the accompanying README.md document
#
# "IT'S A DISGRACE, BUT THERE YOU ARE."
# -- Pozzo. Samuel Beckett. Waiting for Godot, Act 1.


import RPi.GPIO as GPIO
#import wiringpi
import asyncio
import aioserial
from serial import EIGHTBITS, PARITY_NONE,  STOPBITS_ONE
import time
import subprocess # for call to raspi-gpio
import logging

class RPi:
    TXD1   = 14    #  GPIO.BCM  pin 8
    RXD1   = 15    #  GPIO.BCM  pin 10
    RST    = 4     #  GPIO.BCM  pin 7
    debug  = False #  don't go into debug mode

    def gpiosetup(self):
        #wiringpi.wiringPiSetupGpio()
        # aux light is 7 in wiringpi, 4 in BCM gpio coordinates
        #wiringpi.digitalWrite(RST, 0)  # light the AUX light

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        #GPIO.setup(self.RST,GPIO.OUT,initial=GPIO.LOW)
        #time.sleep(0.25)  # reset at least 100ms
        GPIO.setup(self.RST,GPIO.OUT,initial=GPIO.HIGH)

        if self.debug:
            print('GPIO setup mode')
            subprocess.run(["raspi-gpio", "get", '4,14,15'])

    def __del__(self):
        GPIO.cleanup()
        if self.debug:
            print("In RPi destructor.")

    def __init__(self, debug=False):
        self.debug = debug
        self.gpiosetup()


myPi  = RPi(debug=True)
time.sleep(0.1)

try:
    aio: aioserial.AioSerial = aioserial.AioSerial(port='/dev/ttyS0',
                                               baudrate=115200,
                                               parity=PARITY_NONE,
                                               bytesize = EIGHTBITS,
                                               stopbits = STOPBITS_ONE,
                                               timeout = None)
except aioserial.SerialException:
        logging.error(aioserial.SerialException)
        raise aioserial.SerialException


async def read_print(aio: aioserial.AioSerial):
    msg : bytes = await aio.read_until_async(expected = aioserial.LF)
    print(msg.decode(errors='ignore'))


async def ATcmd(aio: aioserial.AioSerial,  cmd: str = ''):
    print("In ATcmd("+cmd+")")
    command = 'AT' + ('+' if len(cmd) > 0 else '') + cmd + '\r\n'
    count : int  = await aio.write_async(bytes(command, 'utf8'))
    msg : bytes = await aio.read_until_async(expected = aioserial.LF)
    print(msg.decode(errors='ignore'))


# state "machines" for the response
rcv_table = [b'+',b'R',b'C',b'V',b'=']
err_table = [b'+',b'E',b'R',b'R',b'=']

async def rcv(aio: aioserial.AioSerial):
    print("In rcv()")

    # Read data from the module

    # NOTE: AT+RCV is NOT a valid command.
    # The module emits "+RCV=w,x,y,z" when it has received a packet
    # To test the +ERR= logic, uncomment the following
    # count : int  = await aio.write_async(bytes('AT+RCV\r\n', 'utf8'))
    # This generates the response b'+ERR=4\r\n'. Otherwise, leave commented

    response = ''
    state = 0  # from 0 to 4 corresponding to +RCV or +ERR
    state_table = rcv_table
    response_len = 0

    while True:
        if aio.inWaiting() > 0: # nonzero = number of characters ready
            # read one byte at a time
            data = await aio.read_async(size=1)
            #print("read:{} state:{}".format(data, state))
            # you are in states < 5 or state 5
            if state < len(state_table):
                if state_table[state] == data:
                    state += 1 # advance the state index
                else:
                    if state == 1 and data == err_table[1]:
                       # Swap out the receive table
                       # for the error table
                       state_table = err_table
                       state += 1 # advance the state index
                    else:
                       response_len = 0 # this hasn't changed
                       response = '' # hasn't changed
                       state = 0 # start over!
                       # Assume good faith, grudgingly
                       state_table = rcv_table
            else:
                # state 5. Accumulate until '\n'
                # responses cannot be larger than 240 bytes
                # add an exception for this case

                response += str(data,'utf8')
                # To keep computing len(response) wastes energy
                # increment instead
                response_len += 1

                if response_len > 240:
                    # This "shouldn't" happen, but "shouldn't"
                    # is often meaningless in programming ...
                    logging.error("Response exceeds 240 characters:{}.".format(response))
                    response = ''
                    response_len = 0
                    state = 0
                    state_table = rcv_table
                    continue

                # If you made it here, the msg is <= 240 chars
                if data == b'\n':

                    if state_table == err_table:
                        logging.error("+ERR={}".format(response))

                        response = ''
                        response_len = 0
                        state = 0
                        state_table = rcv_table
                        continue

                    # The following five lines are adapted from
                    # https://github.com/wybiral/micropython-rylr/blob/master/rylr.py
                    addr, n, response = response.split(',', 2)
                    n = int(n)
                    _data = response[:n]
                    response = response[n+1:]
                    rssi, snr = response.split(',')
                    print("addr:{} len:{} data:{} rssi:{} snr:{}".format(addr,n,_data,rssi,snr[:-2]))

                    # no matter what happened, start over
                    # forget the past. Be a  Markovian.
                    response = '' # reset the response string
                    response_len = 0
                    state = 0     # start over start over
                    state_table = rcv_table


if __name__ == "__main__":

    async def producer(queue, aio: aioserial.AioSerial):
        await queue.put(await ATcmd(aio))
        await queue.put(await ATcmd(aio, 'MODE?'))
        await queue.put(await ATcmd(aio, 'IPR?'))
        await queue.put(await ATcmd(aio, 'PARAMETER?'))
        await queue.put(await ATcmd(aio, 'BAND=915125000'))
        await queue.put(await ATcmd(aio, 'BAND?'))
        await queue.put(await ATcmd(aio, 'ADDRESS?'))
        await queue.put(await ATcmd(aio, 'NETWORKID?'))
        await queue.put(await ATcmd(aio, 'CPIN?'))
        await queue.put(await ATcmd(aio, 'CRFOP=1'))
        await queue.put(await ATcmd(aio, 'CRFOP?'))
        await queue.put(await ATcmd(aio, 'SEND=0,12,de, CALLSIGN'))
        await queue.put(await rcv(aio))
        await queue.put(None)  # a termination signal

    async def consumer(queue):
        while True:
            item = await queue.get()
            if item is None:
                break


    async def main():
        queue = asyncio.Queue()
        await asyncio.gather(producer(queue, aio), consumer(queue))
        await asyncio.sleep(0.01)

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("CTRL-C! Exiting!")

    finally:
        aio.close()
