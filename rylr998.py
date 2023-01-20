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
import curses.textpad as textpad
import _curses
#import datetime
import sys


class rylr998:
    TXD1   = 14    # GPIO.BCM  pin 8
    RXD1   = 15    # GPIO.BCM  pin 10
    RST    = 4     # GPIO.BCM  pin 7
    debug  = False # By default, don't go into debug mode

    aio : aioserial.AioSerial   = None  # asyncio serial port

    # default values for the serial port constructor below

    port     ='/dev/ttyS0'
    baudrate = 115200
    parity   = PARITY_NONE
    bytesize = EIGHTBITS
    stopbits = STOPBITS_ONE
    timeout  = None

    # state "machines" for various AT command and receiver responses
    
    ADDR_table  = [b'+',b'A',b'D',b'D',b'R',b'E',b'S',b'S',b'=']
    BAND_table  = [b'+',b'B',b'A',b'N',b'D',b'=']
    CRFOP_table = [b'+',b'C',b'R',b'F',b'O',b'P',b'=']
    ERR_table   = [b'+',b'E',b'R',b'R',b'=']
    IPR_table   = [b'+',b'I',b'P',b'R',b'=']
    MODE_table  = [b'+',b'M',b'O',b'D',b'E',b'=']
    NETID_table = [b'+',b'N',b'E',b'T',b'W',b'O',b'R',b'K',b'I',b'D',b'=']
    OK_table    = [b'+',b'O',b'K']
    PARAM_table = [b'+',b'P',b'A',b'R',b'A',b'M',b'E',b'T',b'E',b'R',b'=']
    RCV_table   = [b'+',b'R',b'C',b'V',b'='] # receive is the default "state"
    UID_table   = [b'+',b'U',b'I',b'D',b'=']
    VER_table   = [b'+',b'V',b'E',b'R',b'=']

    # initial receive buffer state

    rxbuf = ''  # string response
    rxlen = 0

    state = 0   # index into the current state table
    state_table = RCV_table # start state for the "machine"

    # initial transmit buffer state

    txbuf = ''     # tx buffer
    txlen = 0      # tx buffer length

    # reset the receive buffer state
    # NOTE: the receive buffer state is part of the RYLR998 object
    # but the curses receive window state is maintained in the xcvr() function
    def rxbufReset(self) -> None:
        self.rxbuf = ''
        self.rxlen = 0
        self.state = 0
        self.state_table = self.RCV_table # the default since RCV takes priority

    # reset the transmit buffer state
    # NOTE: the transmit buffer state is part of the RYRL998 object
    # but the curses transmit window state is maintained in the xcvr() function 

    def txbufReset(self) -> None:
        self.txbuf = '' # clear tx buffer
        self.txlen = 0  # txlen is zero
        self.txcol = 0  # start at relative column zero

    def gpiosetup(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        GPIO.setup(self.RST,GPIO.OUT,initial=GPIO.HIGH) # this is the default anyway

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


    # Transceiver function
    #
    # This is the main loop. The transceiver function xcvr(scr) is designed
    # to prioritize receving and parsing command responses from the RYLR998
    # over transmission and configuration. This is done one character at
    # a time, by maintining the receive buffer, receive window, transmit
    # buffer and transmit windows separately.
    #
    # Listening takes priority over talking. Therefore this code is
    # woke by definition and cannot be cancelled by moralizing busybodies 
    # and tiresome scolds under penaty of exclusion from the MIT license. 
    # Assuming this is even possible. I doubt it because of all of the 
    # other open source code licenses this code relies on. OK, maybe 
    # the code isn't entirely woke, because I plan to enable a sleep mode 
    # to conserve power. Just forget this entire paragraph and keep reading.

    async def xcvr(self, scr : _curses.window) -> None:
        # color pair initialization constants
        YELLOW_BLACK = 1
        GREEN_BLACK  = 2  # our pallete is off bear with me
        BLUE_BLACK   = 3
        RED_BLACK    = 4
        BLACK_PINK   = 5  # 
          
        def init_curses() -> None:
            cur.savetty() # this has become necessary here  
            cur.raw()
            cur.start_color()
            cur.use_default_colors()
            # define a fg,bg pair
            cur.init_pair(YELLOW_BLACK, cur.COLOR_YELLOW, cur.COLOR_BLACK)
            # and another fg,bg pair (don't ask why BLUE is GREEN and conversely)
            cur.init_pair(GREEN_BLACK, cur.COLOR_BLUE,  cur.COLOR_BLACK)
            # and yet another
            cur.init_pair(BLUE_BLACK, cur.COLOR_GREEN,  cur.COLOR_BLACK)
            # and yet another -- this is for errors
            cur.init_pair(RED_BLACK, cur.COLOR_RED,  cur.COLOR_BLACK)
            # an approximation
            cur.init_pair(BLACK_PINK, cur.COLOR_MAGENTA, cur.COLOR_BLACK)
            scr.nodelay(True) # non-blocking getch()

        # ATcmd() is only called within the transceiver loop, 
        # so it is an inner function. The transceiver loop parses 
        # the response to AT commands from the RYLR998

        async def ATcmd(cmd: str = '') -> int:
            if self.debug:
                print("In ATcmd("+cmd+")")
            command = 'AT' + ('+' if len(cmd) > 0 else '') + cmd + '\r\n'
            count : int  = await self.aio.write_async(bytes(command, 'utf8'))
            return count

        
        init_curses()


        # receive window initialization
        # keep track of the cursor in each window
        #rectangle(win, uly, ulx, lry, lrx)

        textpad.rectangle(scr,0,0,21,41)
        rxwin = scr.derwin(20,40,1,1)
        rxwin.scrollok(True)
        # This changes the foreground color 
        rxwin.bkgd(' ', cur.color_pair(YELLOW_BLACK))
        rxrow = 0   # rxwin_y relative window coordinates
        rxcol = 0   # rxwin_x
        
        # receive buffer and state reset
        self.rxbufReset()
 
        # transmit window initialization
        textpad.rectangle(scr, 23,0, 25, 41)
        txwin = scr.derwin(1,40,24,1)
        txwin.nodelay(True)
        # txwin cursor coordinates
        txrow = 0   # txwin_y
        txcol = 0   # txwin_x
        txwin.move(txrow, txcol)
        txwin.bkgd(' ', cur.color_pair(YELLOW_BLACK))
        txwin.refresh()

        self.txbufReset()

        # show the rectangles
        scr.refresh()



        # Brace yourself: we are close to entering the main loop

        # NOTE: AT+RCV is NOT a valid command.
        # The RYLR998 module emits "+RCV=w,x,y,z" when it has received a packet
        # To test the +ERR= logic, uncomment the following
        # count : int  = await ATcmd('RCV')
        # This generates the response b'+ERR=4\r\n'. Otherwise, leave commented.
        # Other functions can be tested, such as the query functions below
        # Only one such function can be uncommented at a time, or an ERR=4
        # condition will result.
        # count : int  = await ATcmd('UID?')
        # count : int  = await ATcmd('VER?')
        # this next causes trouble to debug
        # count : int  = await ATcmd('RESET')
        # count : int  = await ATcmd('BAND?')
        count : int  = await ATcmd('BAND=915125000')
        #count : int  = await ATcmd('NETWORKID?')
        # Add test of > 240 character string
        # Add English interpretations of the ERR conditions

        # This is the moment of truth, as evidenced by the "while True:" below

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
                            self.state += 1  # advance the state
                            match data:
                                case b'A':
                                    self.state_table = self.ADDR_table
                                case b'B':
                                    self.state_table = self.BAND_table
                                case b'C':
                                    self.state_table = self.CRFOP_table
                                case b'E':
                                    self.state_table = self.ERR_table
                                case b'I':
                                    self.state_table = self.IPR_table
                                case b'M':
                                    self.state_table = self.MODE_table
                                case b'N':
                                    self.state_table = self.NETID_table # like a net group
                                case b'O':
                                    self.state_table = self.OK_table # inadvertently omitted previously!
                                case b'P':
                                    self.state_table = self.PARAM_table
                                case b'R':
                                    self.state_table = self.RCV_table  # this won't happen but...
                                case b'U':
                                    self.state_table = self.UID_table
                                case b'V':
                                    self.state_table = self.VER_table
                                case _:
                                    self.rxbufReset() # beats me start over
                        else:
                            # in this case, the state is 0 and you are lost
                            # or greater than 1 and you are lost
                            self.rxbufReset() 

                    continue  # parsing output takes priority over input

                else:
                    # self.state == len(self.state_table). 
                    # accumulate data into rxbuf after the '=' sign until  '\n'
                    # The OK does not have an equal sign, so it vanishes.

                    # advance the rx buffer 
                    self.rxbuf += str(data,'utf8')
                    self.rxlen += 1 # superior to calling len()

                    if self.rxlen > 240:
                        # The hardware is supposed to catch this error 
                        logging.error("Response exceeds 240 characters:{}.".format(self.rxbuf))
                        # NOTE TO SELF: handle the rxwindow as well.

                        self.rxbufReset()
                        continue

                    # If you made it here, the msg is <= 240 chars

                    if data == b'\n':
                        # remove the carriage return, newline from rxbuf
                        self.rxbuf = self.rxbuf[:-2]
                        self.rxlen -= 2

                        # handlers for the curses display go here 
                          
                        match self.state_table:
                            case self.ADDR_table:
                                pass
                            case self.BAND_table:
                                rxwin.addnstr(rxrow, rxcol, "Freq = " + self.rxbuf +" Hz", self.rxlen+10, cur.color_pair(BLUE_BLACK))
                            case self.CRFOP_table:
                                pass
                            case self.ERR_table:
                                rxwin.addnstr(rxrow, rxcol,"+ERR={}".format(self.rxbuf), self.rxlen+7, cur.color_pair(RED_BLACK))
                            case self.IPR_table:
                                pass
                            case self.MODE_table:
                                pass
                            case self.OK_table:
                                rxwin.addnstr(rxrow, rxcol, "+OK", 3, cur.color_pair(BLUE_BLACK))
                            case self.NETID_table:
                                pass
                            case self.PARAM_table:
                                pass
                            case self.RCV_table:
                                # The following five lines are adapted from
                                # https://github.com/wybiral/micropython-rylr/blob/master/rylr.py
                                
                                addr, n, self.rxbuf = self.rxbuf.split(',', 2)
                                n = int(n)
                                msg = self.rxbuf[:n]
                                self.rxbuf = self.rxbuf[n+1:]
                                rssi, snr = self.rxbuf.split(',')
                                # the address, rssi and the snr should go in separate "windows"
                                rxwin.addstr(rxrow, rxcol, "@:{} len:{} data:{} rssi:{} snr:{}".format(addr,n,msg,rssi,snr), cur.color_pair(BLACK_PINK))
                            case self.UID_table:
                                pass
                            case self.VER_table:
                                pass
                            case _:
                                rxwin.addstr(rxrow, rxcol, "ERROR. Call Tech Support!", cur.color_pair(RED_BLACK))
                         
                        # advance the rx window row and check if scrolling
                        rxrow = min(19, rxrow+1)
                        rxcol = 0
                        rxwin.refresh()

                        # also return to the txwin
                        txwin.move(txrow, txcol)
                        txwin.refresh()

                        self.rxbufReset() # reset the receive buffer state and assume RCV -- this is necessary

                        # falling through to the non-blocking getch() is OK here 
                        #continue # unless you change your mind--see how the code performs

                    else: # not a newline yet. Prioritize receive and responses from the module
                        continue # still accumulating response from /dev/ttyS0, keep listening

            # at long last, you can speak
            ch = txwin.getch()
            if ch == -1: # no character
                continue
            elif ch == 3: # CTRL-C
                cur.noraw() # go back to cooked mode
                cur.resetty() # restore the terminal
                raise KeyboardInterrupt

            elif   ch == ord(b'\x1b'): # b'x1b' is ESC
                # clear the transmit buffer
                txwin.clear()
                txcol = 0
                self.txbufReset()

            elif ch == ord('\n'):
                if self.txlen > 0:
                    # here you need the address from an initialization step!
                    # the send is assuming address == 0.

                    await ATcmd('SEND=0,'+str(self.txlen)+','+self.txbuf)
                    rxwin.addnstr(rxrow, rxcol,"{}".format(self.txbuf), self.txlen, cur.color_pair(YELLOW_BLACK))
                    rxrow = min(19, rxrow+1)
                    rxwin.refresh()
                    # these were outside the condition 4 spaces left
                    txcol=0
                    txwin.move(txrow, txcol) # cursor to tx initial input position
                    txwin.clear()
                    self.txbufReset()

            elif ch == ord(b'\x08'): # Backspace
                self.txbuf = self.txbuf[:-1]
                self.txlen = max(0, self.txlen-1)
                txcol = max(0, txcol-1)
                txwin.delch(txrow, txcol)
                txwin.refresh()
            else:
                if self.txlen < 40:
                    self.txbuf += str(chr(ch))
                else:
                    # overwrite the end if at position 40
                    self.txbuf = self.txbuf[:-1] + str(chr(ch))
                self.txlen = min(40, self.txlen+1) #  
                txcol = min(39, txcol+1)


if __name__ == "__main__":

    rylr  = rylr998(debug=False)

    try:
        # how's this for an idiom
        asyncio.run(cur.wrapper(rylr.xcvr))

    except KeyboardInterrupt:
        print("! CTRL-C entered, gotta book. 73!")

    finally:
        print("またね！")
