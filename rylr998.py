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
import subprocess # for call to raspi-gpio
import logging
import curses as cur
import _curses
import datetime
import sys

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


    # state "machines" for various AT command and receiver responses
 
    RCV_table =    [b'+',b'R',b'C',b'V',b'=']
    ERR_table =    [b'+',b'E',b'R',b'R',b'=']
    OK_table =     [b'+',b'O',b'K']
    MODE_table =   [b'+',b'M',b'O',b'D',b'E',b'=']
    BAND_table =   [b'+',b'B',b'A',b'N',b'D',b'=']

    rxbuf = ''  # string response
    rxlen = 0
    state_table = RCV_table

    txbuf = ''     # tx  buffer
    txlen = 0      # tx buffer length

    def resetstate(self) -> None:
        self.rxbuf = ''
        self.rxlen = 0
        self.state = 0
        self.state_table = self.RCV_table # the default since RCV takes priority

    def resettxbuf(self) -> None:
        self.txbuf = '' # clear tx buffer
        self.txlen = 0  # txlen is zero

    def gpiosetup(self) -> None:
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


    # we always call this function from the transceiver function below
    async def ATcmd(self, cmd: str = ''):
        if self.debug:
            print("In ATcmd("+cmd+")")
        command = 'AT' + ('+' if len(cmd) > 0 else '') + cmd + '\r\n'
        count : int  = await self.aio.write_async(bytes(command, 'utf8'))
        # use the transceiver loop to parse the response from the RYLR998


    # Transceiver function
    # This is the main loop. Receving takes priority over transmission
    async def xcvr(self, stdscr : _curses.window) -> None:
        # Read data from the module

        # NOTE: AT+RCV is NOT a valid command.
        # The module emits "+RCV=w,x,y,z" when it has received a packet
        # To test the +ERR= logic, uncomment the following
        # count : int  = await aio.write_async(bytes('AT+RCV\r\n', 'utf8'))
        # This generates the response b'+ERR=4\r\n'. Otherwise, leave commented

        self.resetstate()
        self.resettxbuf()
        stdscr.nodelay(1) # non-blocking getch()

        while True:
            #print(datetime.datetime.now())
            if self.aio.in_waiting > 0: # nonzero = # of characters ready
                # read one byte at a time
                data = await self.aio.read_async(size=1)
                if self.debug:
                    print("read:{} state:{}".format(data, self.state))

                # parsing a response
                if self.state < len(self.state_table):
                    if self.state_table[self.state] == data:
                        self.state += 1 # advance the state index
                    else:
                        if self.state == 1:
                            if  data == self.ERR_table[1]:
                                # Swap out the receive table
                                # for the error table
                                self.state_table = self.ERR_table
                                self.state += 1 # advance the state index
                            elif data == self.OK_table[1]:
                                self.state_table = self.OK_table
                                self.state += 1 # advance the state index
                            elif data == self.BAND_table[1]:
                                self.state_table = self.BAND_table
                                self.state += 1 # advance the state index
                            else:
                                self.resetstate() # give up. Dunno what it is
                        else:
                            self.resetstate()
                else:
                    # self.state == len(self.state_table). Acc until '\n'
                    # responses cannot be larger than 240 bytes
                    # add an exception for this case

                    self.rxbuf += str(data,'utf8')
                    # To keep computing len(response) wastes energy
                    # increment instead
                    self.rxlen += 1

                    if self.rxlen > 240:
                        # The hardware is supposed to catch this error 
                        
                        logging.error("Response exceeds 240 characters:{}.".format(self.rxbuf))
                        self.resetstate()
                        continue

                    # If you made it here, the msg is <= 240 chars
                    if data == b'\n':

                        if self.state_table == self.ERR_table:
                            logging.error("+ERR={}".format(self.rxbuf))
                            self.resetstate()
                            continue
                     
                        if self.state_table == self.OK_table:
                            self.resetstate()
                            continue

                        # This case is for RCV only
                        # The following five lines are adapted from
                        # https://github.com/wybiral/micropython-rylr/blob/master/rylr.py
                        if self.state_table == self.RCV_table:
                            addr, n, self.rxbuf = self.rxbuf.split(',', 2)
                            n = int(n)
                            msg = self.rxbuf[:n]
                            self.rxbuf = self.rxbuf[n+1:]
                            rssi, snr = self.rxbuf.split(',')
                            print("addr:{} len:{} data:{} rssi:{} snr:{}".format(addr,n,msg,rssi,snr[:-2]))

                            self.resetstate()
                            # fall through OK here
                    else: # not a newline yet. Prioritize receive
                        continue # still accumulating response from /dev/ttyS0, stay in receive

            # curses getch() with NODELAY is a foregone conclusion
            # because this is a curses program
            ch = stdscr.getch()
            if ch == -1:
                continue
            if  ch == ord(b'\x1b'): # b'x1b' is ESC
                # clear the transmit buffer
                self.resettxbuf()
            elif ch == ord(b'\n'):
                if self.txlen > 0:
                    await self.ATcmd('SEND=0,'+str(self.txlen)+','+self.txbuf)
                self.resettxbuf()
                continue
            elif ch == ord(b'\x08'): # Backspace
                self.txbuf = self.txbuf[:-1]
                self.txlen = max(0, self.txlen-1)
            else:
                self.txbuf += str(chr(ch))
                self.txlen += 1
                if self.debug:
                    print(chr(ch), self.txbuf, self.txlen)


if __name__ == "__main__":

    rylr  = rylr998(debug=True)

    try:
        asyncio.run(cur.wrapper(rylr.xcvr))

    except KeyboardInterrupt:
        print("CTRL-C! Exiting!")

    finally:
        print("that's all folks")
