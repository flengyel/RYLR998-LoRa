#!/usr/bin/env python3
# -*- coding: utf8 -*-
#
# A demo texting program in python for the REYAX RYLR998 LoRa® module.
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

#import RPi.GPIO as GPIO
import asyncio
import aioserial
from serial import EIGHTBITS, PARITY_NONE,  STOPBITS_ONE


import logging
import curses as cur
import _curses
import curses.ascii

#import datetime
import locale
locale.setlocale(locale.LC_ALL, '')
#stdscr.addstr(0, 0, mystring.encode('UTF-8'))

existGPIO = True
try:
    import subprocess # for call to raspi-gpio
    import RPi.GPIO as GPIO
except RuntimeError:
    existGPIO = False

import argparse 
import re # regular expressions
import sys

parser = argparse.ArgumentParser()

parser.add_argument('--debug', action='store_true', help = 'log DEBUG information')

# rylr998 configuration argument group

DEFAULT_ADDR_INT = 0 # type int
DEFAULT_BAND = '915125000'
DEFAULT_PORT = '/dev/ttyS0'
DEFAULT_BAUD = '115200'
DEFAULT_CRFOP = '22'


rylr998_config = parser.add_argument_group('rylr998 config')
rylr998_config.add_argument('--addr', required=False, type=int, choices=range(0,65536),
                   metavar='[0-65535]', dest='addr', default = DEFAULT_ADDR_INT,
                   help='Module address (0-65535). Default is ' + str(DEFAULT_ADDR_INT)) 

def bandcheck(n : str) -> str:
    f = int(n)
    if f < 902125000 or f > 927875000:
        logging.error("Frequency must be in range (902125000-927875000)")
        raise argparse.ArgumentTypeError("Frequency must be in range (902125000-927875000)")
    return n

rylr998_config.add_argument('--band', required=False, type=bandcheck, 
                   metavar='[902125000-927875000]', dest='band', default = DEFAULT_BAND, # subtle type
                            help='Module frequency (902125000-927875000) in Hz. Default: ' + DEFAULT_BAND) 

def pwrcheck(n : str) -> str:
    p = int(n)
    if p < 0 or p > 22:
        logging.error("Power output must be in range (0-22)")
        raise argparse.ArgumentTypeError("Power output must be in range (0-22)")
    return n

rylr998_config.add_argument('--crfop', required=False, type=pwrcheck, 
                            metavar='[0-22]', dest='crfop', default = DEFAULT_CRFOP, 
                            help='RF pwr out (0-22) in dBm. NOTE: If set, tx at least once to rx again. Default: ' + DEFAULT_CRFOP)

# serial port configuration argument group
serial_config = parser.add_argument_group('serial port config')

uartPattern = re.compile('^/dev/ttyS\d{1,3}$')
def uartcheck(s : str) -> str:
    if uartPattern.match(s):
        return s
    raise argparse.ArgumentTypeError("Serial Port device name not of the form ^/dev/ttyS\d{1,3}$")

serial_config.add_argument('--port', required=False, type=uartcheck, metavar='[/dev/ttyS0-/dev/ttyS999]',
                           default = DEFAULT_PORT, dest='port',
                           help='Serial port device name. Default: '+ DEFAULT_PORT)


baudrates = ['300', '1200', '4800', '9600', '19200', '28800', '38400', '57600',  '115200']

baudchoices = '('+ baudrates[0]
for i in range(1, len(baudrates)):
    baudchoices +=  '|' + baudrates[i]
baudchoices +=')'

serial_config.add_argument('--baud', required=False, type=str, 
                           metavar=baudchoices,
                           default = DEFAULT_BAUD, dest='baud', choices = baudrates,
                           help='Serial port baudrate. Default: '+DEFAULT_BAUD)

class Display:
    # color pair initialization constants
    WHITE_BLACK  = 0  # built in cannot change 
    YELLOW_BLACK = 1
    GREEN_BLACK  = 2  # our pallete is off bear with me
    BLUE_BLACK   = 3
    RED_BLACK    = 4  # Pardon the kpop reference below
    BLACK_PINK   = 5  # received text is really magenta on black
    WHITE_RED    = 6
    WHITE_GREEN  = 7          

    ONESEC       = 1
    HALFSEC      = 0.5
    FOURTHSEC    = 0.25
    TENTHSEC     = 0.1
    CENTISEC     = 0.01 

    # status window (stwin) labels
    # coordinates are relative to the stwin
    TXRX_LBL      = " LoRa "
    TXRX_LEN  = 6
    #TXRX_ROW = 0 All row numbers are 0
    TXRX_COL  = 0

    ADDR_LBL = "ADDR"
    ADDR_LEN = 4
    ADDR_COL = 8

    RSSI_COL = 21
    RSSI_LBL = "RSSI"
    RSSI_LEN = 4

    SNR_COL = 31
    SNR_LBL = "SNR"
    SNR_LEN = 3


    # this needs to be part of the Display class
    rxrow = 0   # rxwin_y relative window coordinates
    rxcol = 0   # rxwin_x
    rxwin = None 

    def __init__(self, scr) -> None:
        cur.savetty() # this has become necessary here  
        cur.raw()  # this is unavoidable
        scr.nodelay(True) # non-blocking getch()
        scr.bkgd(' ', cur.color_pair(self.WHITE_BLACK))

        # we compromise by setting the ESC delay to 1 msec
        # we do not want to miss any received characters
        cur.set_escdelay(1) # An eternity for a CPU.

        cur.start_color()
        cur.use_default_colors()

        cur.init_color(cur.COLOR_RED,1000,0,0)
        cur.init_color(cur.COLOR_GREEN,0,1000,0)
        cur.init_color(cur.COLOR_BLUE,0,0,1000)

        # define fg,bg pairs
        cur.init_pair(self.YELLOW_BLACK, cur.COLOR_YELLOW,  cur.COLOR_BLACK) # user text
        cur.init_pair(self.GREEN_BLACK, cur.COLOR_BLUE, cur.COLOR_BLACK)
        cur.init_pair(self.BLUE_BLACK, cur.COLOR_GREEN, cur.COLOR_BLACK) # status indicator
        cur.init_pair(self.RED_BLACK, cur.COLOR_RED, cur.COLOR_BLACK) # errors
        cur.init_pair(self.BLACK_PINK, cur.COLOR_MAGENTA, cur.COLOR_BLACK) # received text
        cur.init_pair(self.WHITE_RED, cur.COLOR_WHITE, cur.COLOR_RED)
        cur.init_pair(self.WHITE_GREEN, cur.COLOR_WHITE, cur.COLOR_GREEN)  

    # receive and transmit window border initialization

    # The next two inner functions restrict access to the receive 
    # and transmit window border variables rxbdr and txbdr, resp., 
    # and return the derived receive and transmit windows 
    # rxwin and txwin, respectively.

    # Relative coordinates are congenial - might remove magic numbers

    def derive_rxwin(self, scr : _curses) -> None:
        rxbdr = scr.derwin(22,42,0,0)
        # window.border([ls[, rs[, ts[, bs[, tl[, tr[, bl[, br]]]]]]]])
        rxbdr.border(0,0,0,0,0,0,cur.ACS_LTEE, cur.ACS_RTEE)
        rxbdr.addch(21,7, cur.ACS_TTEE)
        rxbdr.addch(21,20, cur.ACS_TTEE)
        rxbdr.addch(21,31, cur.ACS_TTEE)
        rxbdr.noutrefresh()
        self.rxwin = rxbdr.derwin(20,40,1,1)

    # move up to avoid overwriting
    def rxScrollUp(self) -> None:
        row, col = self.rxwin.getyx()
        if row == 19:
            self.rxwin.scroll()

    def rxNextRow(self) -> None:
        # set rxrow, rxcol
        row, col = self.rxwin.getyx()
        self.rxrow = min(19, row+1)
        self.rxcol = 0 # never moves

    def rxaddnstr(self, msg, msglen, fg_bg = BLUE_BLACK) -> None:
        self.rxScrollUp()
        self.rxwin.addnstr(self.rxrow, self.rxcol, msg, msglen, cur.color_pair(fg_bg))
        self.rxNextRow()
        self.rxwin.noutrefresh()

    def rxinsnstr(self, msg, msglen, fg_bg = BLUE_BLACK) -> None:
        self.rxScrollUp()
        self.rxwin.insnstr(self.rxrow, self.rxcol, msg, msglen, cur.color_pair(fg_bg))
        self.rxNextRow()
        self.rxwin.noutrefresh()

    def derive_txwin(self, scr : _curses) -> _curses.window:
        txbdr = scr.derwin(3,42,23,0)
        # window.border([ls[, rs[, ts[, bs[, tl[, tr[, bl[, br]]]]]]]])
        txbdr.border(0,0,0,0,cur.ACS_LTEE, cur.ACS_RTEE,0,0)
        txbdr.addch(0,7, cur.ACS_BTEE)
        txbdr.addch(0,20, cur.ACS_BTEE)
        txbdr.addch(0,31, cur.ACS_BTEE)
        txbdr.noutrefresh()
        return txbdr.derwin(1,40,1,1)

    # status "window" setup
    def derive_stwin(self, scr: _curses) -> _curses.window:
        stwin = scr.derwin(1,40,22,1)
        fg_bg = cur.color_pair(self.WHITE_BLACK)
        stwin.bkgd(' ', fg_bg)

        # the first ACS_VLINE lies outside stwin
        scr.vline(22, 0,  cur.ACS_VLINE, 1, fg_bg )
        #stwin.addstr(0, 0, u" LoRa\U000000AE", cur.color_pair(self.WHITE_BLACK)) 
        stwin.addnstr(0, self.TXRX_COL, self.TXRX_LBL, self.TXRX_LEN, fg_bg) 
        stwin.vline(0, 6, cur.ACS_VLINE, 1,  fg_bg)
        stwin.addnstr(0, self.ADDR_COL, self.ADDR_LBL, self.ADDR_COL, fg_bg) 
        stwin.vline(0, 19, cur.ACS_VLINE, 1, fg_bg)

        stwin.addnstr(0, self.RSSI_COL, self.RSSI_LBL, self.RSSI_LEN, fg_bg)
        stwin.vline(0, 30, cur.ACS_VLINE, 1, fg_bg)

        stwin.addnstr(0, self.SNR_COL, self.SNR_LBL, self.SNR_LEN, fg_bg)
        # the last ACS_VLINE lies outside stwin
        scr.vline(22, 41,  cur.ACS_VLINE, 1,  fg_bg)
        return stwin

class rylr998:
    TXD1   = 14    # GPIO.BCM  pin 8
    RXD1   = 15    # GPIO.BCM  pin 10
    RST    = 4     # GPIO.BCM  pin 7

    aio : aioserial.AioSerial   = None  # asyncio serial port

    # default values for the serial port constructor below

    port     = DEFAULT_PORT
    baudrate = DEFAULT_BAUD
    parity   = PARITY_NONE
    bytesize = EIGHTBITS
    stopbits = STOPBITS_ONE
    timeout  = None

    debug  = False # By default, don't go into debug mode

    # RYLR998 configuration parameters 
    addr     = str(DEFAULT_ADDR_INT) # the default
    networkid = '18'
    crfop    = None

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
        self.state_table = self.RCV_table # default since RCV takes priority

    # reset the transmit buffer state
    # NOTE: the transmit buffer state is part of the RYRL998 object
    # the curses transmit window state is maintained in the xcvr() function 

    def txbufReset(self) -> None:
        self.txbuf = '' # clear tx buffer
        self.txlen = 0  # txlen is zero

    # state machine functions

    def in_rcv(self): # I would rather short-circuit inline
        return self.state == 2 and self.state_table == RCV_table
  
    # character differs from RCV_table at position 1 
    # -- change the state table or start over
    def change_state_table(self, data):
        self.state += 1 # advance the state index
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

    def gpiosetup(self) -> None:
        if existGPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(True)
            GPIO.setup(self.RST,GPIO.OUT,initial=GPIO.HIGH) # the default anyway
            #if self.debug:
                #print('GPIO setup mode')
                #subprocess.run(["raspi-gpio", "get", '4,14,15'])

    def __del__(self):
        try:
            self.aio.close() # close the serial port
        except Exception as e:
            logging.error(str(e))

        if existGPIO:
            GPIO.cleanup()   # clean up the GPIO

    def __init__(self, args, parity=PARITY_NONE, bytesize=EIGHTBITS,
                       stopbits= STOPBITS_ONE, timeout=None):

        # NOTE: do not set a variable "self.args"

        # now you can improve this, since only self and args 
        # should be passed to init if a serial port arg group is defined
        # move these arguments into a serial port group.

        self.port = args.port     # the RYLR998 cares about this
        self.baudrate = args.baud # and this (type string!)
        self.parity = parity      # this is fixed
        self.bytesize = bytesize  # so is this
        self.stopbits = stopbits  # and this
        self.timeout = timeout    # and this
        self.debug = args.debug


        # note: self.addr is a str, args.addr is an int
        self.addr = str(args.addr) # set the default
        if  any([arg.startswith('--crfop') for arg in sys.argv[1:]]):                    
            self.crfop = args.crfop

        self.gpiosetup()
        
        try:
            self.aio: aioserial.AioSerial = aioserial.AioSerial(
                                                 port = self.port,
                                                 baudrate = self.baudrate,
                                                 parity = self.parity,
                                                 bytesize = self.bytesize,
                                                 stopbits = self.stopbits,
                                                 timeout = self.timeout)

            logging.info('Opened port '+ self.port + ' at ' + self.baudrate + 'baud') 
        except Exception as e:
            logging.error(str(e))
            exit(1) # quit at this point -- no serial port then no go

    # Transceiver function
    #
    # This is the main loop. The transceiver function xcvr(scr) is designed
    # to prioritize receving and parsing command responses from the RYLR998
    # over transmission and configuration. This is done one character at
    # a time, by maintining the receive buffer, receive window, transmit
    # buffer and transmit windows separately.

    async def xcvr(self, scr : _curses.window) -> None:

        # ATcmd() is only called within the transceiver loop (OUTER LOOP), 
        # so it is an inner function. The OUTER LOOP parses the response 
        # to AT commands from the RYLR998 in two phases, incidentally.

        async def ATcmd(cmd: str = '') -> int:
            command = 'AT' + ('+' if len(cmd) > 0 else '') + cmd + '\r\n'
            count : int  = await self.aio.write_async(bytes(command, 'utf8'))
            return count

        dsply  = Display(scr) 

        # derived window initializations

        dsply.derive_rxwin(scr)
        dsply.rxwin.scrollok(True)

        dsply.rxwin.bkgd(' ', cur.color_pair(dsply.YELLOW_BLACK)) # set bg color
        dsply.rxwin.noutrefresh() # updates occur in one place in the xcvr() loop

        
        # receive buffer and state reset
        self.rxbufReset()
 
        # The LoRa® status indicator turns beet RED if the following is True
        txflag = False # True if and only if transmitting
        stwin = dsply.derive_stwin(scr)
        stwin.noutrefresh()

        # transmit window initialization
        txwin = dsply.derive_txwin(scr)
        txwin.nodelay(True)
        txwin.keypad(True)

        # I'd prefer not timing out ESC, but there is no choice. 
        txwin.notimeout(False) 

        # txwin cursor coordinates
        txrow = 0   # txwin_y
        txcol = 0   # txwin_x
        txwin.move(txrow, txcol)
        txwin.bkgd(' ', cur.color_pair(dsply.YELLOW_BLACK))
        txwin.noutrefresh()
 
        self.txbufReset()
 
        # show the rectangles etc
        scr.noutrefresh()
     
        # Brace yourself: we are approaching the xcvr() loop 

        # NOTE: AT+RCV is NOT a valid command.
        # The RYLR998 module emits "+RCV=w,x,y,z" when it receives a packet
        # To test the +ERR= logic, uncomment the following
        # count : int  = await ATcmd('RCV')
        # This generates the response b'+ERR=4\r\n'. Else, leave commented.

        # this next causes trouble  debug
        # count : int  = await ATcmd('RESET')
        # Add English interpretations of the ERR conditions

        # sorry, these commands have to be enqueued and handled
        # one at a time

        queue = asyncio.Queue()  # no limit
        await queue.put('ADDRESS='+self.addr)  
        await queue.put('NETWORKID='+self.networkid) # this is a str
        await queue.put('BAND='+args.band)
        await queue.put('PARAMETER=9,7,1,12')
        await queue.put('ADDRESS?')
        await queue.put('NETWORKID?')
        await queue.put('BAND?')
        await queue.put('IPR='+self.baudrate)
        # CRFOP=#dBm seems to want a TX before another receive...
        if self.crfop:
            await queue.put('CRFOP='+self.crfop)
            await queue.put('SEND=0,'+str(len(self.crfop)+4)+',pwr:'+self.crfop)

        await queue.put('MODE=0')
        await queue.put('MODE?')
        await queue.put('PARAMETER?') # maybe not properly tested??
        await queue.put('UID?')
        await queue.put('VER?')
        await queue.put('CRFOP?')

        # You are about to participate in a great adventure.
        # You are about to experience the awe and mystery that
        # reaches from the inner functions to THE XCVR LOOP

        dirty = True  # transmit and RCV will set these
        # NOTE: the xcvr() loop updates the display only if 
        # dirty is True.  
        # is at the end of phase 2 parsing of serial output.
        # The dirty flag is set during character handling. 

        # At the beginning of the xcvr loop, 
        # cur.doupdate() is called and the dirty flag is  reset,
        # provided the dirty flag is set. This speeds up the display

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
                if self.debug: # this is buggy
                    logging.info("read:{} state:{}".format(data, self.state))

                # Phase One: parse the fixed portion of the serial port response
                if self.state < len(self.state_table):
                    if self.state_table[self.state] == data:
                        if self.state == 2 and self.state_table == self.RCV_table:
                            stwin.addnstr(0,dsply.TXRX_COL, dsply.TXRX_LBL, dsply.TXRX_LEN, 
                                          cur.color_pair(dsply.WHITE_GREEN))
                            stwin.noutrefresh()
                            # cursor back to tx window to avoid flicker
                            txwin.move(txrow, txcol)  
                            txwin.noutrefresh()
                            dirty = True

                        self.state += 1 # advance the state index
                    else:
                        if self.state == 1:
                            # advance the state index
                            # if the state table cannot be changed
                            # the rx buffer and the state will be reset
                            self.change_state_table(data)
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




                        match self.state_table:
                            case self.ADDR_table:
                                dsply.rxaddnstr("addr: " + self.rxbuf, self.rxlen+6)

                            case self.BAND_table:
                                dsply.rxaddnstr("frequency: " + self.rxbuf +" Hz", self.rxlen+14) 

                            case self.CRFOP_table:
                                dsply.rxaddnstr("power output: {} dBm".format(self.rxbuf), self.rxlen+14)       

                            case self.ERR_table:
                                dsply.rxaddnstr("+ERR={}".format(self.rxbuf), self.rxlen+7, fg_bg=dsply.RED_BLACK)

                            case self.IPR_table:
                                dsply.rxaddnstr("uart: " + self.rxbuf + " baud", self.rxlen+11)

                            case self.MODE_table:
                                dsply.rxaddnstr("mode: " + self.rxbuf, self.rxlen+6)

                            case self.OK_table:
                                if txflag:
                                    # turn the transmit indicator off
                                    stwin.addnstr(0,dsply.TXRX_COL, dsply.TXRX_LBL, dsply.TXRX_LEN, 
                                                  cur.color_pair(dsply.WHITE_BLACK))
                                    stwin.noutrefresh() # yes, that was it
                                    txflag = False
                                else:
                                    dsply.rxaddnstr("+OK", 3)

                            case self.NETID_table:
                                dsply.rxaddnstr("NETWORK ID: " + self.rxbuf, self.rxlen+12) 
                                

                            case self.PARAM_table:
                                _sp, _ba, _co, _pr = self.rxbuf.split(',')
                                dsply.rxaddnstr("spreading factor: {}".format(_sp), len(_sp)+18) 
                                dsply.rxaddnstr("bandwidth: {}".format(_ba), len(_ba)+10)  
                                dsply.rxaddnstr("coding rate: {}".format(_co), len(_co)+13)  
                                dsply.rxaddnstr("preamble: {}".format(_pr), len(_pr)+10)

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
                                    dsply.rxinsnstr(msg, n, fg_bg = dsply.BLACK_PINK)
                                else:
                                    # take advantage of auto scroll if n > 40.
                                    dsply.rxaddnstr(msg, n, fg_bg = dsply.BLACK_PINK) 


                                stwin.addnstr(0,dsply.TXRX_COL, dsply.TXRX_LBL, dsply.TXRX_LEN, 
                                              cur.color_pair(dsply.WHITE_BLACK))

                                # add the ADDRESS, RSSI and SNR to the status window
                                stwin.addstr(0, 13, addr, 
                                             cur.color_pair(dsply.BLUE_BLACK))
                                stwin.addstr(0, 26, rssi, 
                                             cur.color_pair(dsply.BLUE_BLACK))
                                stwin.addstr(0, 36, snr, 
                                             cur.color_pair(dsply.BLUE_BLACK))
                                stwin.noutrefresh()

                            case self.UID_table:
                                dsply.rxaddnstr("UID: " + self.rxbuf, self.rxlen+5) 

                            case self.VER_table:
                                dsply.rxaddnstr("VER: " + self.rxbuf, self.rxlen+5) 
                                

                            case _:
                                dsply.rxaddnstr("ERROR. Call Tech Support!",25, fg_bg = dsply.RED_BLACK) 
                         

                        # also return to the txwin
                        txwin.move(txrow, txcol)
                        txwin.noutrefresh()

                        self.rxbufReset() # reset the receive buffer state and assume RCV -- this is necessary

                        dirty = True    # instead of doupdate() here, use the dirty bit
                        txflag = False

                        continue # The dirty bit logic will update the screen

                    else: # not a newline yet. Prioritize receive and responses from the module
                        if self.rxlen > 240:
                            self.rxbufReset() # this is an error
                        continue # still accumulating chars from serial port, keep listening

            # at long last, you can speak
            ch = txwin.getch()
            if ch == -1: # cat got your tongue? 

                # if you are transmitting, wait for the OK
                # some commands get receive a +OK. Wait for those
                if not txflag and  not queue.empty(): # check if there is a command
                    await ATcmd( await queue.get() )
                    txflag = True  # as if you are transmitting
                continue

            elif ch == cur.ascii.ETX: # CTRL-C
                cur.noraw()     # go back to cooked mode
                cur.resetty()   # restore the terminal
                print("\n")
                return

            elif ch == cur.ascii.ESC: 
                # clear the transmit buffer
                txcol = 0
                self.txbufReset()
                txwin.erase()
                txwin.noutrefresh() # may not be needed
                dirty = True

            elif ch == cur.ascii.LF:
                if self.txlen > 0:
                    # the SEND_COMMAND includes the address 
                    # Don't be silly: you don't have to or want to send only to your address!!!
                    # you could send to some other address
                    await ATcmd('SEND='+self.addr+','+str(self.txlen)+','+self.txbuf)


                    # use insnsstr() here to avoid scrolling if 40 characters (the maximum)
                    if self.txlen == 40:
                        dsply.rxinsnstr(self.txbuf, self.txlen, fg_bg = dsply.YELLOW_BLACK)
                    else:
                        dsply.rxaddnstr(self.txbuf, self.txlen, fg_bg = dsply.YELLOW_BLACK)

                    txcol=0
                    txwin.move(txrow, txcol) # cursor to tx initial input position
                    txwin.clear()
                    txwin.noutrefresh()
                    self.txbufReset()
                   

                    # flash the LoRa® indicator on transmit
                    stwin.addnstr(0,dsply.TXRX_COL, dsply.TXRX_LBL, dsply.TXRX_LEN, 
                                  cur.color_pair(dsply.WHITE_RED))
                    txflag = True       # reset txflag in OK_table logic 
                    stwin.noutrefresh()

                    # really True this time
                    dirty = True

            elif ch == cur.ascii.BS: # Backspace
                self.txbuf = self.txbuf[:-1]
                self.txlen = max(0, self.txlen-1)
                txcol = max(0, txcol-1)
                txwin.delch(txrow, txcol)
                txwin.noutrefresh()
                dirty = True

            elif cur.ascii.isascii(ch):
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

    args = parser.parse_args()
    rylr  = rylr998(args)

    try:
        # how's this for an idiom?
        asyncio.run(cur.wrapper(rylr.xcvr))

    except KeyboardInterrupt: 
        # note that except Exception doesn't catch KeyboardInterrupt
        pass

    finally:
        print("73!") 
