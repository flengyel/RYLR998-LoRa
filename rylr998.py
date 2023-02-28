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
import sys # needed to compensate for argparses argh-parsing

DEFAULT_ADDR_INT = 0 # type int
DEFAULT_BAND = '915000000'
DEFAULT_PORT = '/dev/ttyS0'
DEFAULT_BAUD = '115200'
DEFAULT_CRFOP = '22'
DEFAULT_MODE  = '0'
DEFAULT_NETID = '18'
DEFAULT_SPREADING_FACTOR = '9'
DEFAULT_BANDWIDTH = '7'
DEFAULT_CODING_RATE = '1'
DEFAULT_PREAMBLE = '12'
DEFAULT_PARAMETER = DEFAULT_SPREADING_FACTOR + ',' + DEFAULT_BANDWIDTH + ',' + DEFAULT_CODING_RATE + ',' + DEFAULT_PREAMBLE 

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
    TXRX_ROW = 0 
    TXRX_COL  = 0

    ADDR_LBL = "ADDR"
    ADDR_LEN = 4
    ADDR_COL = 8

    RSSI_COL = 21
    RSSI_LBL = "RSSI"
    RSSI_LEN = 4

    SNR_COL = 32
    SNR_LBL = "SNR"
    SNR_LEN = 3

    VFO_LBL = "VFO"
    VFO_LEN = 3
    VFO_ROW = 2
    VFO_COL = 1

    PWR_LBL = "PWR"
    PWR_LEN = 3
    PWR_ROW = 2
    PWR_COL = 17

    NETID_LBL = "NETWORK ID"
    NETID_LEN = 10
    NETID_ROW = 2
    NETID_COL = 26 

    # this needs to be part of the Display class
    rxrow = 0   # rxwin_y relative window coordinates
    rxcol = 0   # rxwin_x
    rxwin = None 
    bdrwin = None # the outer window.

    def __init__(self, scr) -> None:
        cur.savetty() # this has become necessary here  
        cur.raw()  # raw, almost vegan character handling needed
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

    def borderland(self, scr : _curses) -> None:
        # define the border in one place. Program from outer to inner.
        bdrwin = scr.derwin(28,42,0,0)
        bdrwin.border()
        # Fill in the details

        # receive window border
        bdrwin.addch(21,0, cur.ACS_LTEE)
        bdrwin.hline(21,1,cur.ACS_HLINE,40)
        bdrwin.addch(21,41, cur.ACS_RTEE)
        bdrwin.addch(21,7, cur.ACS_TTEE)
        bdrwin.addch(21,20, cur.ACS_TTEE)
        bdrwin.addch(21,31, cur.ACS_TTEE)

        # status window border and labels
        fg_bg = cur.color_pair(self.WHITE_BLACK)
        bdrwin.addnstr(22, self.TXRX_COL+1, self.TXRX_LBL, 
                         self.TXRX_LEN, fg_bg) 
        bdrwin.vline(22, 6+1, cur.ACS_VLINE, 1,  fg_bg)
        bdrwin.addnstr(22, self.ADDR_COL+1, self.ADDR_LBL, self.ADDR_COL, fg_bg) 
        bdrwin.vline(22, 19+1, cur.ACS_VLINE, 1, fg_bg)

        bdrwin.addnstr(22, self.RSSI_COL+1, self.RSSI_LBL, self.RSSI_LEN, fg_bg)
        bdrwin.vline(22, 30+1, cur.ACS_VLINE, 1, fg_bg)


        bdrwin.addnstr(22, self.SNR_COL+1, self.SNR_LBL, self.SNR_LEN, fg_bg)
        # second line
        bdrwin.addch(23,0, cur.ACS_LTEE)
        bdrwin.hline(23,1,cur.ACS_HLINE,40)
        bdrwin.addch(23,41, cur.ACS_RTEE)

        bdrwin.addch(23,6+1, cur.ACS_BTEE)
        bdrwin.addch(23,19+1, cur.ACS_BTEE)
        bdrwin.addch(23,30+1, cur.ACS_BTEE)

        bdrwin.addnstr(24, self.VFO_COL+1,
                      self.VFO_LBL, self.VFO_LEN, fg_bg)

        bdrwin.addnstr(24, self.PWR_COL+1,
                      self.PWR_LBL, self.PWR_LEN, fg_bg)

        bdrwin.addnstr(24, self.NETID_COL+1,
                      self.NETID_LBL, self.NETID_LEN, fg_bg)


        bdrwin.addch(23,16,cur.ACS_TTEE)
        bdrwin.addch(24,16,cur.ACS_VLINE)
        bdrwin.addch(23,25,cur.ACS_TTEE)
        bdrwin.addch(24,25,cur.ACS_VLINE)


        # transmit window border
        # third line
        bdrwin.addch(25,0, cur.ACS_LTEE)
        bdrwin.hline(25,1,cur.ACS_HLINE,40)
        bdrwin.addch(25,41, cur.ACS_RTEE)

        bdrwin.addch(25,16, cur.ACS_BTEE)
        bdrwin.addch(25,25, cur.ACS_BTEE)

        bdrwin.noutrefresh()
        self.bdrwin = bdrwin


    def derive_rxwin(self) -> None:
        #rxbdr = scr.derwin(22,42,0,0)
        # window.border([ls[, rs[, ts[, bs[, tl[, tr[, bl[, br]]]]]]]])
        self.rxwin = self.bdrwin.derwin(20,40,1,1)
        self.rxwin.scrollok(True)
        self.rxwin.bkgd(' ', cur.color_pair(self.YELLOW_BLACK)) # set bg color
        self.rxwin.noutrefresh() # updates occur in one place in the xcvr() loop


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

    def derive_txwin(self) -> _curses.window:
        return self.bdrwin.derwin(1,40,26,1)

    # status "window" setup
    def derive_stwin(self, scr: _curses) -> _curses.window:
        stwin = self.bdrwin.derwin(3,40,22,1)
        fg_bg = cur.color_pair(self.WHITE_BLACK)
        stwin.bkgd(' ', fg_bg)
        return stwin

    def xlateError(self, errCode: str) -> None:
        match errCode:
            case '1':
                errStr = "AT command missing 0x0D 0x0A."
            case '2':
                errStr = "AT command missing 'AT'."
            case '4':
                errStr = "Unknown AT command."
            case '5':
                errStr = "Data length specified does not match the data length."
            case '10':
                errStr = "Transmit time exceeds limit."
            case '12':
                errStr = "CRC error on receive."
            case '13':
                errStr = "TX data exceeds 240 bytes."
            case '14':
                errStr = "Failed to write flash memory."
            case '15':
                errStr = "Unknown failure."
            case '17':
                errStr = "Last TX was not completed."
            case '18':
                errStr = "Preamble value is not allowed."
            case '19':
                errStr = "RX failure. Header error."
            case '20':
                errStr = "Invalid time in MODE 2 setting."
            case _:
                errStr = "Unknown error code."
        errString = "ERR={}: {}".format(errCode, errStr)
        self.rxaddnstr(errString, len(errString), fg_bg=self.RED_BLACK)
        
class rylr998:
    TXD1   = 14    # GPIO.BCM  pin 8
    RXD1   = 15    # GPIO.BCM  pin 10
    RST    = 4     # GPIO.BCM  pin 7

    aio : aioserial.AioSerial   = None  # asyncio serial port

    debug  = False # By default, don't go into debug mode
    reset  = False

    # RYLR998 configuration parameters 
    addr      = str(DEFAULT_ADDR_INT) # the default
    netid     = str(DEFAULT_NETID)
    crfop     = str(DEFAULT_CRFOP) # will be set to None if --crfop is absent because of unexpected module behavior
    mode      = str(DEFAULT_MODE) 
    parameter = str(DEFAULT_PARAMETER) 
    spreading_factor = str(DEFAULT_SPREADING_FACTOR)
    bandwidth = str(DEFAULT_BANDWIDTH)
    coding_rate = str(DEFAULT_CODING_RATE)
    preamble  = str(DEFAULT_PREAMBLE)
    version   = ''
    uid       = '' 

    # state "machines" for various AT command and receiver responses
    
    ADDR_table  = [b'+',b'A',b'D',b'D',b'R',b'E',b'S',b'S',b'=']
    BAND_table  = [b'+',b'B',b'A',b'N',b'D',b'=']
    CRFOP_table = [b'+',b'C',b'R',b'F',b'O',b'P',b'=']
    ERR_table   = [b'+',b'E',b'R',b'R',b'=']
    FACT_table  = [b'+',b'F',b'A',b'C',b'T',b'O',b'R',b'Y'] # reset to factory defaults
    IPR_table   = [b'+',b'I',b'P',b'R',b'=']
    MODE_table  = [b'+',b'M',b'O',b'D',b'E',b'=']
    NETID_table = [b'+',b'N',b'E',b'T',b'W',b'O',b'R',b'K',b'I',b'D',b'=']
    OK_table    = [b'+',b'O',b'K']
    PARAM_table = [b'+',b'P',b'A',b'R',b'A',b'M',b'E',b'T',b'E',b'R',b'=']
    RCV_table   = [b'+',b'R',b'C',b'V',b'='] # receive is the default "state"
#    RESET_table = [b'+',b'R',b'E',b'S',b'E',b'T'] # RESET detected in state 2 if state_table == RCV_table
#    READY_table = [b'+',b'R',b'E',b'A',b'D',b'Y'] # if RESET received, state_table = READY_table
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

    # the state table can be overriden. This is used in the transition
    # from the RESET_table state to the READY_table state.
    def rxbufReset(self, state_table = RCV_table) -> None:
        self.rxbuf = ''
        self.rxlen = 0
        self.state = 0
        self.state_table = state_table # default since RCV takes priority

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
            case b'F': # factory
                self.state_table = self.FACT_table
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

        self.port = args.port     # the RYLR998 cares about this
        self.baudrate = args.baud # and this (type string!)
        self.parity = parity      # this is fixed
        self.bytesize = bytesize  # so is this
        self.stopbits = stopbits  # and this
        self.timeout = timeout    # and this

        self.debug = args.debug
        #self.reset = args.reset   # not much of a command
        self.factory = args.factory  # if factory  reset

        # note: self.addr is a str, args.addr is an int
        self.addr = str(args.addr) # set the default
        # the odd behavior of crfop seems to require this
        if  any([arg.startswith('--crfop') for arg in sys.argv[1:]]):                    
            self.crfop = args.crfop
        else:
            self.crfop = None

        self.mode = str(args.mode)
        self.netid = str(args.netid)

        if any([arg.startswith('--parameter') for arg in sys.argv[1:]]):                    
            self.spreading_factor, self.bandwidth, self.coding_rate, self.preamble = args.parameter.split(',')
            if self.netid != DEFAULT_NETID and self.preamble != 12:
                logging.error('Preamble must be 12 if NETWORKID is not equal to the default ' + DEFAULT_NETID + '.')
                raise argparse.ArgumentTypeError('Preamble must be 12 if NETWORKID is not equal to the default ' + DEFAULT_NETID + '.' )
        else:
            self.parameter = DEFAULT_PARAMETER  # set the default
            self.spreading_factor = str(DEFAULT_SPREADING_FACTOR)
            self.bandwidth        = str(DEFAULT_BANDWIDTH)
            self.coding_rate      = str(DEFAULT_CODING_RATE)
            self.preamble         = str(DEFAULT_PREAMBLE)

        if args.noGPIO:
            existGPIO = False

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


        dsply.borderland(scr)
        # derived window initializations

        dsply.derive_rxwin()
        
        # receive buffer and state reset
        self.rxbufReset()
 
        # The LoRa® status indicator turns beet RED if the following is True
        txflag = False # True if and only if transmitting
        stwin = dsply.derive_stwin(scr)
        stwin.noutrefresh()

        # transmit window initialization
        txwin = dsply.derive_txwin()
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

        # sorry, these commands have to be enqueued and dequeued
        # one at a time within the transceiver loop

        queue = asyncio.Queue()  # no limit

        if self.factory:
            await queue.put('FACTORY')
            await queue.put('DELAY,'+str(dsply.FOURTHSEC))

        await queue.put('IPR='+self.baudrate) #  chicken and egg
        await queue.put('ADDRESS='+self.addr)  
        await queue.put('NETWORKID='+self.netid) # this is a str
        await queue.put('BAND='+args.band)

        if self.crfop:   
            await queue.put('CRFOP='+self.crfop) # the next is needed to receive again!
        await queue.put('PARAMETER='+self.spreading_factor+','+self.bandwidth+','+self.coding_rate+','+self.preamble)

        await queue.put('ADDRESS?')
        await queue.put('BAND?')
        await queue.put('CRFOP?')
        await queue.put('MODE='+self.mode)
        await queue.put('PARAMETER?') 
        await queue.put('UID?')
        await queue.put('VER?')
        await queue.put('NETWORKID?')


        # You are about to participate in a great adventure.
        # You are about to experience the awe and mystery that
        # reaches from the inner functions to THE OUTER LOOP

        dirty = True  # transmit and RCV will set this

        # a state variable is enough to synchronize AT commands
        waitForReply =  False 

        # Hold onto your chair and godspeed. 

        while True:
            # At the beginning of the xcvr loop, 
            # cur.doupdate() is called and the dirty flag is  reset,
            # provided the dirty flag is set. This speeds up the display

            #if self.debug and self.txlen > 0:
            #   s = 'txcol:'+str(txcol)+ ' txlen:'+str(self.txlen) + ' txbuf:' + self.txbuf
            #   dsply.rxaddnstr(s, len(s))
            #   txwin.move(txrow, txcol)
            #   txwin.noutrefresh()
            #   dirty = True

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
                                self.addr = self.rxbuf
                                waitForReply = False

                            case self.BAND_table:
                                dsply.rxaddnstr("frequency: " + self.rxbuf +" Hz", self.rxlen+14) 
                                self.band = self.rxbuf
                                stwin.addnstr(dsply.VFO_ROW, dsply.VFO_COL+4,self.band, 
                                              self.rxlen, cur.color_pair(dsply.WHITE_BLACK))
                                stwin.noutrefresh()
                                waitForReply = False

                            case self.CRFOP_table:
                                dsply.rxaddnstr("power output: {} dBm".format(self.rxbuf), self.rxlen+14)       
                                self.crfop = self.rxbuf
                                stwin.addnstr(dsply.PWR_ROW, dsply.PWR_COL+4,self.crfop, 
                                              self.rxlen, cur.color_pair(dsply.WHITE_BLACK))
                                stwin.noutrefresh()
                                waitForReply = False

                            case self.ERR_table:
                                dsply.xlateError(self.rxbuf)
                                waitForReply = False
                                  
                            case self.FACT_table:
                                dsply.rxaddnstr("Factory defaults", 16)
                                waitForReply = False

                            case self.IPR_table:
                                dsply.rxaddnstr("uart: " + self.rxbuf + " baud", self.rxlen+11)
                                self.baudrate = self.rxbuf
                                waitForReply = False

                            case self.MODE_table:
                                dsply.rxaddnstr("mode: " + self.rxbuf, self.rxlen+6)
                                self.mode = self.rxbuf
                                waitForReply = False

                            case self.OK_table:
                                if txflag:
                                    # turn the transmit indicator off
                                    stwin.addnstr(0,dsply.TXRX_COL, dsply.TXRX_LBL, dsply.TXRX_LEN, 
                                                  cur.color_pair(dsply.WHITE_BLACK))
                                    stwin.noutrefresh() # yes, that was it
                                    txflag = False # will be reset below
                                else:
                                    dsply.rxaddnstr("+OK", 3)
                                waitForReply = False

                            case self.NETID_table:
                                dsply.rxaddnstr("NETWORK ID: " + self.rxbuf, self.rxlen+12) 
                                self.netid = self.rxbuf
                                stwin.addnstr(dsply.NETID_ROW, 37,self.netid, 
                                              self.rxlen, cur.color_pair(dsply.WHITE_BLACK))
                                stwin.noutrefresh()
                                waitForReply = False
                                
                            case self.PARAM_table:
                                self.spreading_factor, self.bandwidth, self.coding_rate, self.preamble = self.rxbuf.split(',', 3)
                                dsply.rxaddnstr("spreading factor: {}".format(self.spreading_factor), len(self.spreading_factor)+18) 
                                dsply.rxaddnstr("bandwidth: {}".format(self.bandwidth), len(self.bandwidth)+11)  
                                dsply.rxaddnstr("coding rate: {}".format(self.coding_rate), len(self.coding_rate)+13)  
                                dsply.rxaddnstr("preamble: {}".format(self.preamble), len(self.preamble)+10)
                                waitForReply = False

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
                                stwin.addstr(0, 13, addr, cur.color_pair(dsply.BLUE_BLACK))
                                stwin.addstr(0, 26, rssi, cur.color_pair(dsply.BLUE_BLACK))
                                stwin.addstr(0, 36, snr, cur.color_pair(dsply.BLUE_BLACK))
                                stwin.noutrefresh()
                                # not waiting for a reply from the module
                                # so we do not reset the waitForReply flag

                            case self.UID_table:
                                dsply.rxaddnstr("UID: " + self.rxbuf, self.rxlen+5) 
                                self.uid = self.rxbuf
                                waitForReply = False

                            case self.VER_table:
                                dsply.rxaddnstr("VER: " + self.rxbuf, self.rxlen+5) 
                                self.version = self.rxbuf
                                waitForReply = False
                                
                            case _:
                                dsply.rxaddnstr("ERROR. Call Tech Support!",25, fg_bg = dsply.RED_BLACK) 
                                waitForReply = False
                         
                        # also return to the txwin
                        txwin.move(txrow, txcol)
                        txwin.noutrefresh()

                        self.rxbufReset() # reset the receive buffer state and assume RCV -- this is necessary

                        dirty = True    # instead of doupdate() here, use the dirty bit
                        # RCV does not reset waitForReply, since there is no AT command i
                        # for which a response is expected

                    continue # The dirty bit logic will update the screen

                   # else: # not a newline yet. Prioritize receive and responses from the module
                   #     if self.rxlen > 240: # hardware should prevent this from occurring.
                   #         self.rxbufReset() # this is an error
                   #     continue # still accumulating chars from serial port, keep listening

            # at long last, you can speak
            ch = txwin.getch()
            if ch == -1: # cat got your tongue? 
                # dequeue AT commands only if not waiting for AT response to finish
                # receive will take priority if you are receiving
                # use a waitForReply.instead of the txflag, which is for the tx indictor
                # check if there is a command
                if not waitForReply and  not queue.empty(): 
                    waitForReply = True
                    cmd = await queue.get()
                    if cmd.startswith('SEND='):
                        # parse the command SEND=#,msglen,msg) 
                        _, _msglen, msg = cmd.split(',', 2) # the 2 here accounts for commas in msg
                        msglen = int(_msglen) # _msglen is a string
                        # use insnsstr() here to avoid scrolling if 40 characters (the maximum)
                        if msglen == 40:
                            dsply.rxinsnstr(msg, msglen, fg_bg = dsply.YELLOW_BLACK)
                        else:
                            dsply.rxaddnstr(msg, msglen, fg_bg = dsply.YELLOW_BLACK)

                        txcol=0
                        txwin.move(txrow, txcol) # cursor to tx initial input position
                        txwin.clear()
                        txwin.noutrefresh()
                        self.txbufReset()

                        # flash the LoRa® indicator on transmit
                        stwin.addnstr(0,dsply.TXRX_COL, dsply.TXRX_LBL, dsply.TXRX_LEN, 
                                  cur.color_pair(dsply.WHITE_RED))
                        stwin.noutrefresh()
                        txflag = True # transmitting 
                        dirty = True # really True this time 
                    elif cmd.startswith('DELAY,'):
                        _,delay = cmd.split(',',1)
                        await asyncio.sleep(float(delay))
                        waitForReply = False # not an AT command!
                        continue # use this to escape
                    await ATcmd( cmd ) # send command to serial port to rylr998
                continue # remember that RCV and AT cmd responses take priority

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
                    # Don't be silly: you don't have to send only to your address!!!
                    # you could send to some other address
                    await queue.put('SEND='+self.addr+','+str(self.txlen)+','+self.txbuf)

            elif ch == cur.KEY_LEFT:
                txcol = max(0, txcol - 1)
                txwin.move(txrow, txcol)
                txwin.noutrefresh()
                dirty = True

            elif ch == cur.KEY_RIGHT:
                txcol = min(txcol+1, self.txlen, 39)
                txwin.move(txrow, txcol)
                txwin.noutrefresh()
                dirty = True

            elif ch == cur.KEY_DC: # Delete
                if txcol >= self.txlen:
                    continue
                # txcol must be to the left of a character to delete somethin  to the right
                self.txbuf = self.txbuf[0:txcol] + self.txbuf[txcol+1:min(40,self.txlen)]
                self.txlen = max(0,min(40, self.txlen)-1)
                txwin.delch(txrow,txcol)
                if self.txlen < 40:
                    txwin.addnstr(txrow, 0, self.txbuf ,self.txlen)
                else:
                    txwin.insnstr(txrow, 0, self.txbuf, self.txlen)
                txwin.move(txrow,txcol)
                txwin.noutrefresh()
                dirty = True

            elif ch == cur.ascii.BS: # Backspace
                self.txbuf = self.txbuf[0:max(0,txcol-1)]+self.txbuf[txcol:self.txlen]
                self.txlen = max(0,txcol-1) + max(0, self.txlen-txcol) 
                txcol= max(0, txcol-1)
                txwin.delch(txrow, txcol)
                if self.txlen < 40:
                    txwin.addstr(txrow, 0, self.txbuf)
                else:
                    txwin.insstr(txrow, 0, self.txbuf)
                txwin.move(txrow, txcol)
                txwin.noutrefresh()
                dirty = True

            elif cur.ascii.isascii(ch):
                if self.txlen == 40 and txcol < 40:
                    continue   # don't change!
                self.txbuf = self.txbuf[0:txcol] + str(chr(ch)) + self.txbuf[txcol:min(39,self.txlen)]
                self.txlen = min(40, self.txlen+1) #  
                #txwin.insnstr(txrow, txcol, str(chr(ch)),1)
                if self.txlen < 40:
                    txwin.addnstr(txrow, 0, self.txbuf ,self.txlen)
                else:
                    txwin.insnstr(txrow, 0, self.txbuf, self.txlen)
                txcol = min(39, txcol+1)
                txwin.move(txrow, txcol)
                txwin.noutrefresh()
                dirty = True

 
# end of the XCVR loop

if __name__ == "__main__":
    import re # regular expressions for argument checking

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help = 'log DEBUG information')
    # reset seems to result in CRC errors on receive. Wait for firmware
    # revision
    #parser.add_argument('--reset', action='store_true', help = 'Software reset')
    parser.add_argument('--factory', action='store_true', help = 'Factory reset to manufacturer defaults. BAND: 915MHz,  UART: 115200, Spreading Factor: 9, Bandwidth: 125kHz (7), Coding Rate: 1, Preamble Length: 12, Address: 0, Network ID: 18, CRFOP: 22')

    parser.add_argument('--noGPIO', action='store_true', help = "Do not use rPI.GPIO module even if available. Useful if using a USB to TTL converter with the RYLR998.")

    # rylr998 configuration argument group

    # defined elsewhere (upstairs)
    #DEFAULT_ADDR_INT = 0 # type int
    #DEFAULT_BAND = '915125000'
    #DEFAULT_PORT = '/dev/ttyS0'
    #DEFAULT_BAUD = '115200'
    #DEFAULT_CRFOP = '22'
    #DEFAULT_MODE = '0'

    rylr998_config = parser.add_argument_group('rylr998 config')

    rylr998_config.add_argument('--addr', required=False, type=int, choices=range(0,65536),
        metavar='[0..65535]', dest='addr', default = DEFAULT_ADDR_INT,
        help='Module address (0..65535). Default is ' + str(DEFAULT_ADDR_INT)) 

    def bandcheck(n : str) -> str:
        f = int(n)
        if f < 902250000 or f > 927750000:
            logging.error("Frequency must be in range (902250000..927750000)")
            raise argparse.ArgumentTypeError("Frequency must be in range (902250000..927750000)")
        return n

    rylr998_config.add_argument('--band', required=False, type=bandcheck, 
        metavar='[902250000..927750000]', dest='band', default = DEFAULT_BAND, # subtle type
        help='Module frequency (902250000..927750000) in Hz. NOTE: the full 33cm ISM band limits 902 MHz and 928 MHz are guarded by the maximum configurable bandwidth of 500 KHz (250 KHz on either side of the configured frequency). See PARAMETER for bandwidth configuration. Default: ' + DEFAULT_BAND) 

    def pwrcheck(n : str) -> str:
        p = int(n)
        if p < 0 or p > 22:
            logging.error("Power output must be in range (0-22)")
            raise argparse.ArgumentTypeError("Power output must be in range (0-22)")
        return n

    rylr998_config.add_argument('--crfop', required=False, type=pwrcheck, 
        metavar='[0..22]', dest='crfop', default = DEFAULT_CRFOP, 
        help='RF pwr out (0..22) in dBm. Default: FACTORY setting of ' + DEFAULT_CRFOP + ' or the last configured value.')


    modePattern = re.compile('^(0)|(1)|(2,(\d{2,5}),(\d{2,5}))$')
    def modecheck(s : str) -> str:
        p =  modePattern.match(s)
        if p is not None:   
            if p.group(1) is not None or p.group(2) is not None:
                return s
            # mode 2
            r_ms = int(p.group(4))
            s_ms = int(p.group(5))  # dumb bug: you overwrote s, which was an int!!
            if r_ms > 29 and r_ms < 60001 and s_ms > 29 and s_ms < 60001:
                return s
        logging.error("Mode must match 0|1|2,30..60000,30..60000")
        raise argparse.ArgumentTypeError("Mode must match 0|1|2,30..60000,30..60000")


    rylr998_config.add_argument('--mode', required=False, type=modecheck,
        metavar='[0|1|2,30..60000,30..60000]', dest='mode', default = DEFAULT_MODE,
        help='Mode 0: transceiver mode. Mode 1: sleep mode. Mode 2,x,y: receive for x msec sleep for y msec and so on, indefinitely. Default: ' + DEFAULT_MODE)

    netidPattern = re.compile('^3|4|5|6|7|8|9|10|11|12|13|14|15|18$')
    def netidcheck(s : str) -> str:
        if netidPattern.match(s):
            return str(s)
        logging.error('NETWORK ID must match (3..15|18)')
        raise argparse.ArgumentTypeError('NETWORK ID must match (3..15|18)')

    rylr998_config.add_argument('--netid', required=False, type=netidcheck,
        metavar='[3..15|18]', dest='netid', default = DEFAULT_NETID,
        help='NETWORK ID. Note: PARAMETER values depend on NETWORK ID. Default: ' + DEFAULT_NETID)

    paramPattern = re.compile('^([7-9]|1[01]),([7-9]),([1-4]),([4-9]|1\d|2[0-5])$')
    def paramcheck(s : str) -> str:
        def sfbw(sf, bw):
            _sf = int(sf)
            _bw = int(bw)
            return ( _bw == 7 and _sf < 10 or _bw == 8 and _sf < 11 or _bw == 9 and _sf < 12)
        if paramPattern.match(s):
            # check constraints other than NETWORK ID
            sf, bw, _, _ = s.split(',')
            if sfbw(sf, bw):
                return s
            logging.error('Incompatible spreading factor and bandwidth values')
            raise argparse.ArgumentTypeError('PARAMETER: incompatible spreading factor and bandwidth values') 
        logging.error('argument must match 7..11,7..9,1..4,4..24 subject to constraints on spreading factor, bandwidth and NETWORK ID')
        raise argparse.ArgumentTypeError('argument must match 7..11,7..9,1..4,4..24 subject to constraints on spreading factor, bandwidth and NETWORK ID')

    rylr998_config.add_argument('--parameter', required=False, type=paramcheck,         metavar='[7..11,7..9,1..4,4..24]', dest='parameter', default=DEFAULT_PARAMETER,
        help='PARAMETER. Set the RF parameters Spreading Factor, Bandwidth, Coding Rate, Preamble. Spreading factor 7..11, default 9. Bandwidth 7..9, where 7 is 125 KHz (only if spreading factor is in 7..9); 8 is 250 KHz (only if spreading factor is in 7..10); 9 is 500 KHz (only if spreading factor is in 7..11). Default bandwidth is 7. Coding rate is 1..4, default 4. Preamble is 4..25 if the NETWORK ID is 18; otherwise the preamble must be 12.  Default: ' + DEFAULT_PARAMETER)

    # serial port configuration argument group
    serial_config = parser.add_argument_group('serial port config')

    uartPattern = re.compile('^/dev/tty(S|USB)\d{1,3}$')
    def uartcheck(s : str) -> str:
        if uartPattern.match(s):
            return s
        raise argparse.ArgumentTypeError("Serial Port device name not of the form ^/dev/tty(S|USB)\d{1,3}$")

    serial_config.add_argument('--port', required=False, type=uartcheck, 
        metavar='[/dev/ttyS0../dev/ttyS999|/dev/ttyUSB0../dev/ttyUSB999]', default = DEFAULT_PORT, dest='port',
        help='Serial port device name. Default: '+ DEFAULT_PORT)

    baudrates = ['300', '1200', '4800', '9600', '19200', '28800', '38400', '57600',  '115200']
    baudchoices = '('+ baudrates[0]
    for i in range(1, len(baudrates)):
        baudchoices +=  '|' + baudrates[i]
    baudchoices +=')'

    serial_config.add_argument('--baud', required=False, type=str, 
        metavar=baudchoices, default = DEFAULT_BAUD, dest='baud', choices = baudrates,
        help='Serial port baudrate. Default: '+DEFAULT_BAUD)

    # you aren't in curses while you parse command line args
    args = parser.parse_args()
    rylr  = rylr998(args) #  even here you aren't in curses

    try:
        asyncio.run(cur.wrapper(rylr.xcvr)) # how's this for an idiom?
    except KeyboardInterrupt: 
        # recall that "except Exception as e" doesn't catch KeyboardInterrupt 
        pass
    finally:
        print("73!") 
