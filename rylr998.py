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
import asyncio
import aioserial
from serial import EIGHTBITS, PARITY_NONE,  STOPBITS_ONE
import time
import subprocess # for call to raspi-gpio
import logging

class rylr998:
    TXD1   = 14    #  GPIO.BCM  pin 8
    RXD1   = 15    #  GPIO.BCM  pin 10
    RST    = 4     #  GPIO.BCM  pin 7
    debug  = False #  don't go into debug mode

    aio : aioserial.AioSerial   = None  # asyncio serial port

    # default values for the serial port constructor
    port     ='/dev/ttyS0'
    baudrate = 115200
    parity   = PARITY_NONE
    bytesize = EIGHTBITS
    stopbits = STOPBITS_ONE
    timeout  = None


    # state "machines" for the response
    rcv_table = [b'+',b'R',b'C',b'V',b'=']
    err_table = [b'+',b'E',b'R',b'R',b'=']
    response = ''  # string response
    response_len = 0
    state_table = rcv_table

    def resetstate(self):
        self.response = ''
        self.response_len = 0
        self.state = 0
        self.state_table = self.rcv_table


    def gpiosetup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        #GPIO.setup(self.RST,GPIO.OUT,initial=GPIO.LOW)
        #time.sleep(0.25)  # reset at least 100ms
        GPIO.setup(self.RST,GPIO.OUT,initial=GPIO.HIGH)

        if self.debug:
            print('GPIO setup mode')
            subprocess.run(["raspi-gpio", "get", '4,14,15'])

    def __del__(self):
        self.aio.close() # close the serial port
        GPIO.cleanup()   # clean up the GPIO

    def __init__(self, port='/dev/ttyS0',baudrate=115200,
                       parity=PARITY_NONE, bytesize=EIGHTBITS,
                       stopbits= STOPBITS_ONE, timeout=None,
                       debug=False):

        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.timeout = timeout
        self.debug = debug

        self.gpiosetup()

        try:
            self.aio: aioserial.AioSerial = aioserial.AioSerial(
                                                 port = self.port,
                                                 baudrate = self.baudrate,
                                                 parity = self.parity,
                                                 bytesize = self.bytesize,
                                                 stopbits = self.stopbits,
                                                 timeout = self.timeout)

        except aioserial.SerialException:
            logging.error(aioserial.SerialException)
            raise aioserial.SerialException


    async def read_print(self):
        msg : bytes = await self.aio.read_until_async(expected = aioserial.LF)
        print(msg.decode(errors='ignore'))


    async def ATcmd(self, cmd: str = ''):
        print("In ATcmd("+cmd+")")
        command = 'AT' + ('+' if len(cmd) > 0 else '') + cmd + '\r\n'
        count : int  = await self.aio.write_async(bytes(command, 'utf8'))
        msg : bytes = await self.aio.read_until_async(expected = aioserial.LF)
        print(msg.decode(errors='ignore'))


    # This function could be a thread.

    async def rcv(self):
        print("In rcv()")

        # Read data from the module

        # NOTE: AT+RCV is NOT a valid command.
        # The module emits "+RCV=w,x,y,z" when it has received a packet
        # To test the +ERR= logic, uncomment the following
        # count : int  = await aio.write_async(bytes('AT+RCV\r\n', 'utf8'))
        # This generates the response b'+ERR=4\r\n'. Otherwise, leave commented
        self.resetstate()

        while True:
            if self.aio.inWaiting() > 0: # nonzero = number of characters ready
                # read one byte at a time
                data = await self.aio.read_async(size=1)
                #print("read:{} state:{}".format(data, self.state))
                # you are in states < 5 or state 5
                if self.state < len(self.state_table):
                    if self.state_table[self.state] == data:
                        self.state += 1 # advance the state index
                    else:
                        if self.state == 1 and data == self.err_table[1]:
                            # Swap out the receive table
                            # for the error table
                            self.state_table = self.err_table
                            self.state += 1 # advance the state index
                        else:
                            self.resetstate()
                else:
                    # state 5. Accumulate until '\n'
                    # responses cannot be larger than 240 bytes
                    # add an exception for this case

                    self.response += str(data,'utf8')
                    # To keep computing len(response) wastes energy
                    # increment instead
                    self.response_len += 1

                    if self.response_len > 240:
                        # This "shouldn't" happen, but "shouldn't"
                        # is often meaningless in programming ...
                        logging.error("Response exceeds 240 characters:{}.".format(response))
                        self.resetstate()
                        continue

                    # If you made it here, the msg is <= 240 chars
                    if data == b'\n':

                        if self.state_table == self.err_table:
                            logging.error("+ERR={}".format(self.response))
                            self.resetstate()
                            continue

                        # The following five lines are adapted from
                        # https://github.com/wybiral/micropython-rylr/blob/master/rylr.py
                        addr, n, self.response = self.response.split(',', 2)
                        n = int(n)
                        msg = self.response[:n]
                        self.response = self.response[n+1:]
                        rssi, snr = self.response.split(',')
                        print("addr:{} len:{} data:{} rssi:{} snr:{}".format(addr,n,msg,rssi,snr[:-2]))

                        # no matter what happened, start over
                        self.resetstate()

if __name__ == "__main__":

    rylr  = rylr998(debug=True)

    async def producer(queue, rylr : rylr998):
        await queue.put(await rylr.ATcmd())
        await queue.put(await rylr.ATcmd('MODE?'))
        await queue.put(await rylr.ATcmd('IPR?'))
        await queue.put(await rylr.ATcmd('PARAMETER?'))
        await queue.put(await rylr.ATcmd('BAND=915125000'))
        await queue.put(await rylr.ATcmd('BAND?'))
        await queue.put(await rylr.ATcmd('ADDRESS?'))
        await queue.put(await rylr.ATcmd('NETWORKID?'))
        await queue.put(await rylr.ATcmd('CPIN?'))
        await queue.put(await rylr.ATcmd('CRFOP=5'))
        await queue.put(await rylr.ATcmd('CRFOP?'))
        await queue.put(await rylr.ATcmd('SEND=0,7,de WXYZ'))
        await queue.put(await rylr.rcv())
        await queue.put(None)  # a termination signal

    async def consumer(queue):
        while True:
            item = await queue.get()
            if item is None:
                break

    async def main():
        queue = asyncio.Queue()
        await asyncio.gather(producer(queue, rylr), consumer(queue))
        await asyncio.sleep(0.01)

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("CTRL-C! Exiting!")

    finally:
        print("that's all folks")
