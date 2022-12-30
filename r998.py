#!/usr/bin/env python3
# An example program for the REYAX RYLR998
# Written by Florian Lengyel, WM2D
#
# Despite the remarkable fact that the software below was
# designed to work predictably for me with the intended
# hardware devices, their software settings and
# interconnections under their documented operating conditions
# (except for the missing "AT" in the "+RCV" command, as
# documented on page 7 of the  "REYAX RYLR998 RYLR498 Lora
# AT COMMAND GUIDE" (c) 2021 REYAX TECHNOLOGY CO., LTD,
# and corrected herein) be advised:
#
# This software is released under an MIT license.
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
#import wiringpi

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


rcv_table = [b'+',b'R',b'C',b'V',b'=']

# just in case we want to parse this
# not absolutely necessary since an error response
# +ERR=number will be caught in the logic below
err_table = [b'+',b'E',b'R',b'R',b'=']

async def rcv(aio: aioserial.AioSerial):
    print("In rcv()")
    count : int  = await aio.write_async(bytes('AT+RCV\r\n', 'utf8'))
    # Read data from the module
    # ignore the initial junk, preamble, etc

    # The following four commands brought to you by
    # INITIAL CONDITIONS

    response = ''
    state = 0  # from 0 to 4 corresponding to +RCV
    state_table = rcv_table
    response_len = 0

    while True:
        if aio.inWaiting() > 0: # number of characters ready
            data = aio.read(size=1) # read one byte at a time
            # you are in states < 5 or state 5
            if state < len(state_table):
                if state_table[state] == data:
                    state += 1 # keep going!
                else:
                    if state == 1 and data == err_table[1]:
                       # My God! It's full of errors!
                       # Swap out the receive table
                       # for the error table
                       state_table = err_table
                       state += 1 # You saw an 'E' instead of 'R'
                       # advance the state index
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
                        logging.error("code from RYLR998:{}".format(response))
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
    await queue.put(await asyncio.sleep(0.01)) # xmt takes time
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
    print("CTRL-C! Dammit Jim! I'm a doctor, not an interrupt handler! Exiting!")

finally:
    aio.close()
