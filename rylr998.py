#!/usr/bin/env python3
#
# A demo texting program in python for the REYAX RYLR998 LoRa module.
# Get on the air with a Rasperry Pi 4 Model B Rev 1.5, a RYLR998 module,  
# five wires and ten female-female GPIO connectors. 
#
# Written by Florian Lengyel, WM2D
#
# This software is released under an MIT license.
# See the accompanying LICENSE.txt file.
#
# The GPIO connections from the Raspberry Pi to the RYLR998 are as follows:
#
# VDD to 3.3V physical pin 1 on the GPIO
# RST to GPIO 4, physical pin 7
# TXD to GPIO 15 RXD1 this is physical pin 10
# RXD to GPIO 14 TXD1 this is physical pin 8
# GND to GND physical pin 9.

# NOTE: GPIO pin 4, physical pin 7 is an OUTPUT pin with level one and 
# pull=NONE. The current configuration works, but can be improved. You 
# could add a pull up resistor, but then it's five wires and a resistor. 
# The REYAX RYLR998 has tolerated my abuse--I mean setup--so far. 
# See the RYLR998 data sheet.
#
# AT commands follow the  "REYAX RYLR998 RYLR498 Lora AT COMMAND GUIDE"
# (c) 2021 REYAX TECHNOLOGY CO., LTD.
#
# Further instructions are available in the accompanying README.md document
#

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
 
    # state machine initial state 

    state = 0   # index into the current state table
    state_table = RCV_table # start state for the "machine"

    # initial receive buffer state

    rxbuf = ''  # string response
    rxlen = 0

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

    def gpiosetup(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        GPIO.setup(self.RST,GPIO.OUT,initial=GPIO.HIGH) # the default anyway

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

    async def xcvr(self, scr : _curses.window) -> None:
        # color pair initialization constants
        WHITE_BLACK  = 0  # built in cannot change 
        YELLOW_BLACK = 1
        GREEN_BLACK  = 2  # our pallete is off bear with me
        BLUE_BLACK   = 3
        RED_BLACK    = 4  # Pardon the kpop reference below
        BLACK_PINK   = 5  # received text is really magenta on black
        WHITE_RED    = 6
        WHITE_GREEN  = 7          

        def init_curses() -> None:
            cur.savetty() # this has become necessary here  
            cur.raw()  # this is unavoidable
            scr.nodelay(True) # non-blocking getch()

            cur.start_color()
            cur.use_default_colors()

            cur.init_color(cur.COLOR_RED, 500,0,0)
            cur.init_color(cur.COLOR_GREEN, 0,500,0)
            cur.init_color(cur.COLOR_BLUE, 0,0,500)


            # define fg,bg pairs
            cur.init_pair(YELLOW_BLACK, cur.COLOR_YELLOW,  cur.COLOR_BLACK) # user text
            cur.init_pair(GREEN_BLACK,  cur.COLOR_BLUE,    cur.COLOR_BLACK)
            cur.init_pair(BLUE_BLACK,   cur.COLOR_GREEN,   cur.COLOR_BLACK) # status indicator
            cur.init_pair(RED_BLACK,    cur.COLOR_RED,     cur.COLOR_BLACK) # errors
            cur.init_pair(BLACK_PINK,   cur.COLOR_MAGENTA, cur.COLOR_BLACK) # received text
            cur.init_pair(WHITE_RED,    cur.COLOR_WHITE,   cur.COLOR_RED)
            cur.init_pair(WHITE_GREEN,  cur.COLOR_WHITE,   cur.COLOR_BLUE)  # BLUE AND GREEN SWAPPED!

        # receive and transmit window border initialization

        # The next two inner functions restrict access to the receive 
        # and transmit window border variables rxbdr and txbdr, resp., 
        # and return the derived receive and transmit windows 
        # rxwin and txwin, respectively.

        # Relative coordinates are congenial - might remove magic numbers

        def derive_rxwin(scr : _curses) -> _curses.window:
            rxbdr = scr.derwin(22,42,0,0)
            # window.border([ls[, rs[, ts[, bs[, tl[, tr[, bl[, br]]]]]]]])
            rxbdr.border(0,0,0,0,0,0,cur.ACS_LTEE, cur.ACS_RTEE)
            rxbdr.addch(21,7, cur.ACS_TTEE)
            rxbdr.addch(21,20, cur.ACS_TTEE)
            rxbdr.addch(21,31, cur.ACS_TTEE)
            rxbdr.noutrefresh()
            return rxbdr.derwin(20,40,1,1)

        def derive_txwin(scr : _curses) -> _curses.window:
            txbdr = scr.derwin(3,42,23,0)
            # window.border([ls[, rs[, ts[, bs[, tl[, tr[, bl[, br]]]]]]]])
            txbdr.border(0,0,0,0,cur.ACS_LTEE, cur.ACS_RTEE,0,0)
            txbdr.addch(0,7, cur.ACS_BTEE)
            txbdr.addch(0,20, cur.ACS_BTEE)
            txbdr.addch(0,31, cur.ACS_BTEE)
            txbdr.noutrefresh()
            return txbdr.derwin(1,40,1,1)

        # ATcmd() is only called within the transceiver loop (XCVR LOOP), 
        # so it is an inner function. The XCVR LOOP parses the response 
        # to AT commands from the RYLR998 in two phases, incidentally.

        async def ATcmd(cmd: str = '') -> int:
            command = 'AT' + ('+' if len(cmd) > 0 else '') + cmd + '\r\n'
            count : int  = await self.aio.write_async(bytes(command, 'utf8'))
            return count
        
        init_curses()

        # keep track of the cursor in each window
        scr.bkgd(' ', cur.color_pair(WHITE_BLACK))

        # derived window initializations

        rxwin = derive_rxwin(scr)
        rxwin.scrollok(True)

        rxwin.bkgd(' ', cur.color_pair(YELLOW_BLACK)) # set bg color
        rxwin.noutrefresh() # updates occur in one place in the XCVR loop

        rxrow = 0   # rxwin_y relative window coordinates
        rxcol = 0   # rxwin_x
        
        # receive buffer and state reset
        self.rxbufReset()
 
        # status "window" setup
        stwin = scr.derwin(1,40,22,1)
        stwin.bkgd(' ', cur.color_pair(WHITE_BLACK))

        # the first ACS_VLINE lies outside stwin
        scr.vline(22, 0,  cur.ACS_VLINE, 1,  cur.color_pair(WHITE_BLACK))
        stwin.addnstr(0, 1, "LoRa", 4, cur.color_pair(WHITE_BLACK)) 
        stwin.vline(0, 6, cur.ACS_VLINE, 1,  cur.color_pair(WHITE_BLACK))
        stwin.addnstr(0, 8, "ADDR", 4, cur.color_pair(WHITE_BLACK)) 
        stwin.vline(0, 19, cur.ACS_VLINE, 1, cur.color_pair(WHITE_BLACK))
        stwin.addnstr(0, 21, "RSSI", 4, cur.color_pair(WHITE_BLACK)) 
        stwin.vline(0, 30, cur.ACS_VLINE, 1, cur.color_pair(WHITE_BLACK))
        stwin.addnstr(0, 32, "SNR", 3, cur.color_pair(WHITE_BLACK)) 
        # the last ACS_VLINE lies outside stwin
        scr.vline(22, 41,  cur.ACS_VLINE, 1,  cur.color_pair(WHITE_BLACK))

        # The LoRa status indicator turns RED if the following is True
        txflag = False # True if and only if transmitting
        stwin.noutrefresh()

        # transmit window initialization
        txwin = derive_txwin(scr)
        txwin.nodelay(True)
        txwin.keypad(True)

        # I'd prefer not timing out ESC, but there is no choice. 
        txwin.notimeout(False) 
        # we compromise by setting the ESC delay to 1 msec
        # we do not want to miss any received characters
        cur.set_escdelay(1) # An eternity for a CPU.
        # txwin cursor coordinates
        txrow = 0   # txwin_y
        txcol = 0   # txwin_x
        txwin.move(txrow, txcol)
        txwin.bkgd(' ', cur.color_pair(YELLOW_BLACK))
        
        self.txbufReset()
 
        # show the rectangles etc
        scr.noutrefresh()
        dirty = True
     
        # NOTE: the xcvr loop updates the display only if 
        # dirty is True. There are no calls to window.refresh(), 
        # only calls to window.noutrefresh() after which the 
        # dirty flag set. At the beginning of the xcvr loop, 
        # cur.doupdate() is called and the dirty flag is  reset,
        # provided the dirty flag is set. This speeds up the display

        # Brace yourself: we are approaching THE XCVR LOOP 

        # NOTE: AT+RCV is NOT a valid command.
        # The RYLR998 module emits "+RCV=w,x,y,z" when it receives a packet
        # To test the +ERR= logic, uncomment the following
        # count : int  = await ATcmd('RCV')
        # This generates the response b'+ERR=4\r\n'. Else, leave commented.

        # Other functions can be tested, such as the query functions below
        # Only one such function can be uncommented at a time, or an ERR=4
        # condition will result. A task queuing mechanism is on the road map,
        # in the cards, a priority of the utmost urgency--when I get to it.
        #
        # count : int  = await ATcmd('UID?')
        # count : int  = await ATcmd('VER?')
        # this next causes trouble  debug
        # count : int  = await ATcmd('RESET')
        # count : int  = await ATcmd('BAND?')
        # count : int  = await ATcmd('BAND=915125000')
        # count : int  = await ATcmd('NETWORKID?')
        # Add English interpretations of the ERR conditions

        # The transmit address is needed
        # A queue of configuration query tasks should preceed the proceedings
        # this is the first as yet unqueued configuration query command.

        count : int = await ATcmd('ADDRESS?')

        # You are about to participate in a great adventure.
        # You are about to experience the awe and mystery that
        # reaches from the inner functions to THE XCVR LOOP

        # Hold onto your chair and godspeed. 

        while True:

            # update the screen only if the dirty bit was set
            if dirty:
                cur.doupdate() # oh baby
                dirty = False # reset the dirty bit

            if self.aio.in_waiting > 0: # nonzero = # of characters ready
                # read and act one byte at a time. Be a Markov process.

                data = await self.aio.read_async(size=1)

                # you could use a debug window -- perhaps
                if self.debug:
                    print("read:{} state:{}".format(data, self.state))

                # Phase One: parse the fixed portion of the serial port response
                if self.state < len(self.state_table):
                    if self.state_table[self.state] == data:
                        self.state += 1 # advance the state index
                        if self.state == 2 and self.state_table == self.RCV_table:
                            stwin.addnstr(0,1, "LoRa", 4, cur.color_pair(WHITE_GREEN))
                            stwin.noutrefresh()
                            dirty = True

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
                                    self.state_table = self.OK_table 
                                case b'P':
                                    self.state_table = self.PARAM_table
                                case b'R':
                                    self.state_table = self.RCV_table  # impossibe! 
                                case b'U':
                                    self.state_table = self.UID_table
                                case b'V':
                                    self.state_table = self.VER_table
                                case _:
                                    self.rxbufReset() # beats me start over
                        else:
                            # in this case, the state is 0 and you are lost
                            # preamble possibly -- or state > 1 and you are lost
                            self.rxbufReset() 

                    continue  # parsing output takes priority over input

                else:
                    # Phase Two: parse the data portion of the response
                    # the precondition for the second parsing phase obtains:
                    # self.state == len(self.state_table). 
                    # accumulate data into rxbuf after the '=' sign until '\n'
                    # The OK does not have an equal sign, so it vanishes.

                    # advance the rx buffer 
                    self.rxbuf += str(data,'utf8')
                    self.rxlen += 1 # superior to calling len()

                    # If you made it here, the msg is <= 240 chars
                    # the hardware ensures this

                    if data == b'\n':
                        # remove the carriage return, newline from rxbuf
                        self.rxbuf = self.rxbuf[:-2]
                        self.rxlen -= 2

                        # move up to avoid overwriting
                        # A subtle bug was introduced with the txflag.
                        # The guarded code below assumes that a line will 
                        # be added to the rxwin, a condition that fails
                        # during transmit when only the LoRa indicator is
                        # updated in the status window stwin, and nothing 
                        # in the rxwin is updated.. 

                        if not txflag or self.state_table != self.OK_table:
                            row, col = rxwin.getyx() 
                            if row == 19:
                                rxwin.scroll()

                        match self.state_table:
                            case self.ADDR_table:
                                rxwin.addnstr(rxrow, rxcol, "Addr = " + self.rxbuf, self.rxlen+7, cur.color_pair(BLUE_BLACK))
                                rxwin.noutrefresh()  

                            case self.BAND_table:
                                rxwin.addnstr(rxrow, rxcol, "Freq = " + self.rxbuf +" Hz", self.rxlen+10, cur.color_pair(BLUE_BLACK))
                                rxwin.noutrefresh()  

                            case self.CRFOP_table:
                                rxwin.addstr(rxrow, rxcol, "Pwr = {} dBm".format( self.rxbuf), cur.color_pair(BLUE_BLACK))
                                rxwin.noutrefresh()  

                            case self.ERR_table:
                                rxwin.addnstr(rxrow, rxcol,"+ERR={}".format(self.rxbuf), self.rxlen+7, cur.color_pair(RED_BLACK))
                                rxwin.noutrefresh()  

                            case self.IPR_table:
                                pass

                            case self.MODE_table:
                                pass

                            case self.OK_table:
                                if txflag:
                                    stwin.addnstr(0,1, "LoRa", 4, cur.color_pair(WHITE_BLACK))
                                    stwin.noutrefresh() # yes, that was it
                                    txflag = False
                                else:
                                    rxwin.addnstr(rxrow, rxcol, "+OK", 3, cur.color_pair(BLUE_BLACK))
                                    rxwin.noutrefresh()
                                dirty = True  # no matter what happens

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

                                if n == 40:
                                    # prevent auto scrolling if EOL at the
                                    # end of the window
                                    rxwin.insnstr(rxrow, rxcol, msg, n, cur.color_pair(BLACK_PINK))
                                else:
                                    # otherwise, take advantage of auto scroll
                                    # if n > 40.
                                    rxwin.addnstr(rxrow, rxcol, msg, n, cur.color_pair(BLACK_PINK))

                                rxwin.noutrefresh() 

                                # add the ADDRESS, RSSI and SNR to the status window
                                stwin.addnstr(0,1, "LoRa", 4, cur.color_pair(WHITE_BLACK))
                                stwin.addstr(0, 13, addr, cur.color_pair(BLUE_BLACK))
                                stwin.addstr(0, 26, rssi, cur.color_pair(BLUE_BLACK))
                                stwin.addstr(0, 36, snr, cur.color_pair(BLUE_BLACK))
                                stwin.noutrefresh()

                            case self.UID_table:
                                pass

                            case self.VER_table:
                                pass

                            case _:
                                rxwin.addstr(rxrow, rxcol, "ERROR. Call Tech Support!", cur.color_pair(RED_BLACK))
                                rxwin.noutrefresh()  
                         
                        #  Long lines will scroll automatically

                        row, col = rxwin.getyx()
                        rxrow = min(19, row+1)
                        rxcol = 0 # never moves

                        # also return to the txwin
                        txwin.move(txrow, txcol)
                        txwin.noutrefresh()
                        dirty = True

                        self.rxbufReset() # reset the receive buffer state and assume RCV -- this is necessary

                        # falling through to the non-blocking getch() is OK here 
                        #continue # unless you change your mind--see how the code performs

                    else: # not a newline yet. Prioritize receive and responses from the module
                        continue # still accumulating response from /dev/ttyS0, keep listening

            # at long last, you can speak
            ch = txwin.getch()
            if ch == -1: # cat got your tongue? no character
                continue

            elif ch == 3: # CTRL-C
                cur.noraw()     # go back to cooked mode
                cur.resetty()   # restore the terminal
                raise KeyboardInterrupt

            elif ch == ord(b'\x1b'): # b'\x1b' is ESC
                # clear the transmit buffer
                txcol = 0
                self.txbufReset()
                txwin.erase()
                dirty = True

            elif ch == ord('\n'):
                if self.txlen > 0:
                    # need address from initialization 
                    await ATcmd('SEND=0,'+str(self.txlen)+','+self.txbuf)

                    row, col = rxwin.getyx()
                    if row == 19:
                       rxwin.scroll() # scroll up if at the end

                    # use insnsstr() here to avoid scrolling if 40 characters (the maximum)
                    if self.txlen == 40:
                        rxwin.insnstr(rxrow, rxcol, self.txbuf, self.txlen, cur.color_pair(YELLOW_BLACK))
                    else:
                        rxwin.addnstr(rxrow, rxcol, self.txbuf, self.txlen, cur.color_pair(YELLOW_BLACK))

                    row, col = rxwin.getyx()
                    rxrow = min(19, row+1)
                    rxcol = 0
                    rxwin.noutrefresh()

                    txcol=0
                    txwin.move(txrow, txcol) # cursor to tx initial input position
                    txwin.clear()
                    self.txbufReset()


                    # flash the LoRa indicator on transmit
                    stwin.addnstr(0,1, "LoRa", 4, cur.color_pair(WHITE_RED))
                    txflag = True       # reset txflag in OK_table logic 
                    stwin.noutrefresh()

                    # really True this time
                    dirty = True

            elif ch == ord(b'\x08'): # Backspace
                self.txbuf = self.txbuf[:-1]
                self.txlen = max(0, self.txlen-1)
                txcol = max(0, txcol-1)
                txwin.delch(txrow, txcol)
                txwin.noutrefresh()
                dirty = True

            else:
                if not cur.ascii.isascii(ch):
                   continue

                if self.txlen < 40:
                    self.txbuf += str(chr(ch))
                else:
                    # overwrite the end if at position 40
                    self.txbuf = self.txbuf[:-1] + str(chr(ch))
                self.txlen = min(40, self.txlen+1) #  
                txcol = min(39, txcol+1)
                txwin.noutrefresh()
                dirty = True

# end of the XCVR loop

if __name__ == "__main__":

    rylr  = rylr998(debug=False)

    try:
        # how's this for an idiom?
        asyncio.run(cur.wrapper(rylr.xcvr))

    except KeyboardInterrupt:
        print(" Gotta book. 73!")

    finally:
        print("またね！") # ROMAJI mettane ENGLISH see you.
