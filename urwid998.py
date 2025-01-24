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

import asyncio
from serial import EIGHTBITS, PARITY_NONE,  STOPBITS_ONE
import logging
import curses as cur
import _curses
import curses.ascii
import urwid
import platform
from src.core.serial import SerialManager
from display import Display

# Platform detection
PLATFORM = platform.system()
IS_WINDOWS = PLATFORM == 'Windows'
IS_RASPBERRY_PI = PLATFORM == 'Linux' and platform.machine().startswith('arm')

if IS_WINDOWS:
    import sys
    print("Windows is not supported for urwid integration. Please use Raspberry Pi.")
    sys.exit(1)

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


import locale
locale.setlocale(locale.LC_ALL, '')

_exist_gpio = True
try:
    import subprocess # for call to raspi-gpio
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    _exist_gpio = False

import argparse 
import sys # needed to compensate for argparse's arg-parsing
        
class RYLR998:

    exist_gpio = _exist_gpio
    TXD1   = 14    # GPIO.BCM  pin 8
    RXD1   = 15    # GPIO.BCM  pin 10
    RST    = 4     # GPIO.BCM  pin 7

    serial: SerialManager = None
    
    debug  = False # By default, don't go into debug mode
    reset  = False

    # RYLR998 configuration parameters 
    addr      = str(DEFAULT_ADDR_INT) # the default
    netid     = str(DEFAULT_NETID)
    pwr       = str(DEFAULT_CRFOP) # will be set to None if --pwr is absent because of unexpected module behavior
    mode      = str(DEFAULT_MODE) 
    parameter = str(DEFAULT_PARAMETER) 
    spreading_factor = str(DEFAULT_SPREADING_FACTOR)
    bandwidth = str(DEFAULT_BANDWIDTH)
    coding_rate = str(DEFAULT_CODING_RATE)
    preamble  = str(DEFAULT_PREAMBLE)
    version   = ''
    uid       = '' 

    # state "machines" for various AT command and receiver responses
    
    ADDR_TABLE  = [b'+',b'A',b'D',b'D',b'R',b'E',b'S',b'S',b'=']
    BAND_TABLE  = [b'+',b'B',b'A',b'N',b'D',b'=']
    CRFOP_TABLE = [b'+',b'C',b'R',b'F',b'O',b'P',b'=']
    ERR_TABLE   = [b'+',b'E',b'R',b'R',b'=']
    FACT_TABLE  = [b'+',b'F',b'A',b'C',b'T',b'O',b'R',b'Y'] # reset to factory defaults
    IPR_TABLE   = [b'+',b'I',b'P',b'R',b'=']
    MODE_TABLE  = [b'+',b'M',b'O',b'D',b'E',b'=']
    NETID_TABLE = [b'+',b'N',b'E',b'T',b'W',b'O',b'R',b'K',b'I',b'D',b'=']
    OK_TABLE    = [b'+',b'O',b'K']
    PARAM_TABLE = [b'+',b'P',b'A',b'R',b'A',b'M',b'E',b'T',b'E',b'R',b'=']
    RCV_TABLE   = [b'+',b'R',b'C',b'V',b'=']  # receive is the default "state"
#   RESET_table = [b'+',b'R',b'E',b'S',b'E',b'T'] # RESET detected in state 2 if state_table == RCV_table
#   READY_table = [b'+',b'R',b'E',b'A',b'D',b'Y'] # if RESET received, state_table = READY_table
    UID_TABLE   = [b'+',b'U',b'I',b'D',b'=']
    VER_TABLE   = [b'+',b'V',b'E',b'R',b'=']
 
    # state machine initial state 

    state = 0   # index into the current state table
    state_table = RCV_TABLE # start state for the "machine"

    # initial receive buffer state

    rx_buf = ''  # string response
    rx_len = 0

    # initial transmit buffer state

    tx_buf = ''     # tx buffer
    tx_len = 0      # tx buffer length

    # reset the receive buffer state
    # NOTE: the receive buffer state is part of the RYLR998 object
    # but the curses receive window state is maintained in the xcvr() function

    # the state table can be overriden. This is used in the transition
    # from the RESET_table state to the READY_table state.
    def rx_buf_reset(self, state_table = RCV_TABLE) -> None:
        self.rx_buf = ''
        self.rx_len = 0
        self.state = 0
        self.state_table = state_table # default since RCV takes priority

    # reset the transmit buffer state
    # NOTE: the transmit buffer state is part of the RYRL998 object
    # the curses transmit window state is maintained in the xcvr() function 

    def tx_buf_reset(self) -> None:
        self.tx_buf = '' # clear tx buffer
        self.tx_len = 0  # tx_len is zero

    # state machine functions

    def in_rcv(self): # I would rather short-circuit inline
        return self.state == 2 and self.state_table == self.RCV_TABLE
  
    # character differs from RCV_table at position 1 
    # -- change the state table or start over
    def change_state_table(self, data):
        self.state += 1 # advance the state index
        match data:
            case b'A':
                self.state_table = self.ADDR_TABLE
            case b'B':
                self.state_table = self.BAND_TABLE
            case b'C':
                self.state_table = self.CRFOP_TABLE
            case b'E':
                self.state_table = self.ERR_TABLE
            case b'F': # factory
                self.state_table = self.FACT_TABLE
            case b'I':
                self.state_table = self.IPR_TABLE
            case b'M':
                self.state_table = self.MODE_TABLE
            case b'N':
                self.state_table = self.NETID_TABLE # like a net group
            case b'O':
                self.state_table = self.OK_TABLE 
            case b'P':
                self.state_table = self.PARAM_TABLE
            case b'R':
                self.state_table = self.RCV_TABLE  # impossibe! 
            case b'U':
                self.state_table = self.UID_TABLE
            case b'V':
                self.state_table = self.VER_TABLE
            case _:
                self.rx_buf_reset() # beats me start over

    def gpio_setup(self) -> None:
        if self.exist_gpio:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(True)
            GPIO.setup(self.RST,GPIO.OUT,initial=GPIO.HIGH) # the default anyway
            #if self.debug:
                #print('GPIO setup mode')
                #subprocess.run(["raspi-gpio", "get", '4,14,15'])

    def __del__(self):
        try:
            if self.serial:
                self.serial.close()
        except Exception as e:
            logging.error(str(e))

        if self.exist_gpio:
            GPIO.cleanup()  # clean up the GPIO


    def __init__(self, args):

        self.port = args.port     # the RYLR998 cares about this
        self.baudrate = args.baud # and this (type string!)
        self.debug = args.debug
        self.factory = args.factory

        # note: self.addr is a str, args.addr is an int
        self.addr = str(args.addr) # set the default
        # the odd behavior of crfop seems to require this
        if  any([arg.startswith('--pwr') for arg in sys.argv[1:]]):                    
            self.pwr = args.pwr
        else:
            self.pwr = None

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
            self.exist_gpio = False

        self.gpio_setup()

        try:
            self.serial = SerialManager(self.port, self.baudrate)
        except Exception as e:
            logging.error(str(e))
            exit(1)

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

        async def at_cmd(cmd: str = '') -> int:
            command = f"AT{'+' if len(cmd) > 0 else ''}{cmd}\r\n"
            count: int = await self.serial.write(bytes(command, 'utf8'))
            return count
        
        dsply  = Display(scr) 

        # Platform-specific urwid setup
        evl = urwid.AsyncioEventLoop(loop=asyncio.get_event_loop())
        txt = urwid.Text("RYLR998")
        widget = urwid.Filler(txt)
        
        if IS_WINDOWS:
            screen = urwid.raw_display.Screen()
        else:
            # Linux/Raspberry Pi can use default screen
            screen = None
            
        loop = urwid.MainLoop(
            widget, 
            event_loop=evl,
            screen=screen
        )
        loop.start()


         
        # The LoRa® status indicator turns beet RED if the following is True
        tx_flag = False # True if and only if transmitting
        # txwin cursor coordinates
        tx_row = 0   # txwin_y
        tx_col = 0   # txwin_x
        dsply.txwin.move(tx_row, tx_col)
        dsply.txwin.noutrefresh()

        self.tx_buf_reset()
 
        # show the rectangles etc
        scr.noutrefresh()
     
        # Brace yourself: we are approaching the xcvr() loop 

        # NOTE: AT+RCV is NOT a valid command.
        # The RYLR998 module emits "+RCV=w,x,y,z" when it receives a packet
        # To test the +ERR= logic, uncomment the following
        # count : int  = await at_cmd('RCV')
        # This generates the response b'+ERR=4\r\n'. Else, leave commented.

        # this next causes trouble  debug
        # count : int  = await at_cmd('RESET')
        # Add English interpretations of the ERR conditions

        # sorry, these commands have to be enqueued and dequeued
        # one at a time within the transceiver loop

        queue = asyncio.Queue()  # no limit


        if self.factory:
            await queue.put('FACTORY')
            await queue.put(f"DELAY,{str(dsply.FOURTHSEC)}")

        await queue.put(f"IPR={self.baudrate}") #  chicken and egg
        await queue.put(f"ADDRESS={self.addr}")  
        await queue.put(f"NETWORKID={self.netid}") # this is a str
        await queue.put(f"BAND={args.band}")

        if self.pwr:   
            await queue.put(f"CRFOP={self.pwr}") # the next is needed to receive again!
        await queue.put(f"PARAMETER={self.spreading_factor},{self.bandwidth},{self.coding_rate},{self.preamble}")

        await queue.put('ADDRESS?')
        await queue.put('BAND?')
        await queue.put('CRFOP?')
        await queue.put(f"MODE={self.mode}")
        await queue.put('PARAMETER?') 
        await queue.put('UID?')
        await queue.put('VER?')
        await queue.put('NETWORKID?')


        # You are about to participate in a great adventure.
        # You are about to experience the awe and mystery that
        # reaches from the inner functions to THE OUTER LOOP

        dirty = True  # transmit and RCV will set this

        # a state variable is enough to synchronize AT commands
        wait_for_reply =  False 

        # Hold onto your chair and godspeed. 
        try:
            while True:
            # At the beginning of the xcvr loop, 
            # cur.doupdate() is called and the dirty flag is  reset,
            # provided the dirty flag is set. This speeds up the display

                if dirty:
                    cur.doupdate() # oh baby
                    dirty = False # reset the dirty bit

                if self.serial.has_data():  # Changed from self.aio.in_waiting
                    # read and act one byte at a time. Be a Markov process.
                    data = await self.serial.read_byte()  # Changed from self.aio.read_async
                    # you could use a debug window -- perhaps
                    if self.debug: # this is buggy
                        logging.info("read:{} state:{}".format(data, self.state))

                    # Phase One: parse the fixed portion of the serial port response
                    if self.state < len(self.state_table):
                        if self.state_table[self.state] == data:
                            if self.state == 2 and self.state_table == self.RCV_TABLE:
                                dsply.stwin.addnstr(0,dsply.TXRX_COL, dsply.TXRX_LBL, dsply.TXRX_LEN, 
                                            cur.color_pair(dsply.WHITE_GREEN))
                                dsply.stwin.noutrefresh()
                                # cursor back to tx window to avoid flicker
                                dsply.txwin.move(tx_row, tx_col)  
                                dsply.txwin.noutrefresh()
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
                                self.rx_buf_reset() 

                        continue  # parsing output takes priority over input
                    else:
                        # Phase Two: parse the data portion of the response
                        # the precondition for the second parsing phase obtains:
                        # self.state == len(self.state_table). 

                        # accumulate data into rx_buf after the '=' sign until '\n'
                        # The OK does not have an equal sign, so it vanishes.

                        # advance the rx buffer 
                        self.rx_buf += str(data,'utf8')
                        self.rx_len += 1 # superior to calling len()

                        # If you made it here, the msg is <= 240 chars
                        # the hardware ensures this

                        if data == b'\n':
                            # remove the carriage return, newline from rx_buf
                            self.rx_buf = self.rx_buf[:-2]
                            self.rx_len -= 2

                            match self.state_table:
                                case self.ADDR_TABLE:
                                    dsply.rxaddnstr(f"addr: {self.rx_buf}", self.rx_len+6)
                                    self.addr = self.rx_buf
                                    wait_for_reply = False

                                case self.BAND_TABLE:
                                    dsply.rxaddnstr(f"frequency: {self.rx_buf} Hz", self.rx_len+15) 
                                    self.band = self.rx_buf
                                    dsply.stwin.addnstr(dsply.VFO_ROW, dsply.VFO_COL+4,self.band, 
                                                self.rx_len, cur.color_pair(dsply.WHITE_BLACK))
                                    dsply.stwin.noutrefresh()
                                    wait_for_reply = False

                                case self.CRFOP_TABLE:
                                    dsply.rxaddnstr(f"power output: {self.rx_buf} dBm", self.rx_len+18)       
                                    self.pwr = self.rx_buf
                                    dsply.stwin.addnstr(dsply.PWR_ROW, dsply.PWR_COL+4,self.pwr, 
                                                self.rx_len, cur.color_pair(dsply.WHITE_BLACK))
                                    dsply.stwin.noutrefresh()
                                    wait_for_reply = False

                                case self.ERR_TABLE:
                                    dsply.xlateError(self.rx_buf)
                                    wait_for_reply = False
                                  
                                case self.FACT_TABLE:
                                    dsply.rxaddnstr("Factory defaults", 16)
                                    wait_for_reply = False

                                case self.IPR_TABLE:
                                    dsply.rxaddnstr(f"uart: {self.rx_buf} baud", self.rx_len+11)
                                    self.baudrate = self.rx_buf
                                    wait_for_reply = False

                                case self.MODE_TABLE:
                                    dsply.rxaddnstr(f"mode: {self.rx_buf}", self.rx_len+6)
                                    self.mode = self.rx_buf
                                    wait_for_reply = False
        

                                case self.OK_TABLE:
                                    if tx_flag:
                                        # turn the transmit indicator off
                                        dsply.stwin.addnstr(0,dsply.TXRX_COL, dsply.TXRX_LBL, dsply.TXRX_LEN, 
                                                    cur.color_pair(dsply.WHITE_BLACK))
                                        dsply.stwin.noutrefresh() # yes, that was it
                                        tx_flag = False # will be reset below
                                    else:
                                        dsply.rxaddnstr("+OK", 3)
                                    wait_for_reply = False
                                
                                case self.NETID_TABLE:
                                    dsply.rxaddnstr(f"NETWORK ID: {self.rx_buf}", self.rx_len+12) 
                                    self.netid = self.rx_buf
                                    dsply.stwin.addnstr(dsply.NETID_ROW, 37,self.netid, 
                                                self.rx_len, cur.color_pair(dsply.WHITE_BLACK))
                                    dsply.stwin.noutrefresh()
                                    wait_for_reply = False

                                
                                case self.PARAM_TABLE:
                                    self.spreading_factor, self.bandwidth, self.coding_rate, self.preamble = self.rx_buf.split(',', 3)
                                    dsply.rxaddnstr(f"spreading factor: {self.spreading_factor}", len(self.spreading_factor)+18) 
                                    dsply.rxaddnstr(f"bandwidth: {self.bandwidth}", len(self.bandwidth)+11)  
                                    dsply.rxaddnstr(f"coding rate: {self.coding_rate}", len(self.coding_rate)+13)  
                                    dsply.rxaddnstr(f"preamble: {self.preamble}", len(self.preamble)+10)
                                    wait_for_reply = False

                                case self.RCV_TABLE:
                                    # The following five lines are adapted from
                                    # https://github.com/wybiral/micropython-rylr/blob/master/rylr.py
                                
                                    addr, n, self.rx_buf = self.rx_buf.split(',', 2)
                                    n = int(n)
                                    msg = self.rx_buf[:n]
                                    self.rx_buf = self.rx_buf[n+1:]
                                    rssi, snr = self.rx_buf.split(',')

                                    if n == 40:
                                        # prevent auto scrolling if EOL at the
                                        # end of the window
                                        dsply.rxinsnstr(msg, n, fg_bg = dsply.BLACK_PINK)
                                    else:
                                        # take advantage of auto scroll if n > 40.
                                        dsply.rxaddnstr(msg, n, fg_bg = dsply.BLACK_PINK) 

                                    dsply.stwin.addnstr(0,dsply.TXRX_COL, dsply.TXRX_LBL, dsply.TXRX_LEN, 
                                                        cur.color_pair(dsply.WHITE_BLACK))

                                    # add the ADDRESS, RSSI and SNR to the status window
                                    dsply.stwin.addstr(0, 13, addr, cur.color_pair(dsply.BLUE_BLACK))
                                    dsply.stwin.addstr(0, 26, rssi, cur.color_pair(dsply.BLUE_BLACK))
                                    dsply.stwin.addstr(0, 36, snr, cur.color_pair(dsply.BLUE_BLACK))
                                    dsply.stwin.noutrefresh()
                                    # not waiting for a reply from the module
                                    # so we do not reset the waitForReply flag

                                    # if echoing the received message, delay 0.25 sec
                                    if args.echo:
                                        await queue.put(f"DELAY,{str(dsply.FOURTHSEC)}")
                                        await queue.put(f"SEND={addr},{str(n)},{msg}")

                                case self.UID_TABLE:
                                    dsply.rxaddnstr(f"UID: {self.rx_buf}", self.rx_len+5) 
                                    self.uid = self.rx_buf
                                    wait_for_reply = False


                                case self.VER_TABLE:
                                    dsply.rxaddnstr(f"VER: {self.rx_buf}", self.rx_len+5) 
                                    self.version = self.rx_buf
                                    wait_for_reply = False
                                
                                case _:
                                    dsply.rxaddnstr("ERROR. Call Tech Support!",25, fg_bg = dsply.RED_BLACK) 
                                    wait_for_reply = False
                         
                            # also return to the txwin
                            dsply.txwin.move(tx_row, tx_col)
                            dsply.txwin.noutrefresh()

                            self.rx_buf_reset() # reset the receive buffer state and assume RCV -- this is necessary

                            dirty = True    # instead of doupdate() here, use the dirty bit
                            # RCV does not reset waitForReply, since there is no AT command 
                            # for which a response is expected

                        continue # The dirty bit logic will update the screen

                    # else: # not a newline yet. Prioritize receive and responses from the module
                    #     if self.rx_len > 240: # hardware should prevent this from occurring.
                    #         self.rxbufReset() # this is an error
                    #     continue # still accumulating chars from serial port, keep listening

                # at long last, you can speak
                ch = dsply.txwin.getch()
                if ch == -1: # cat got your tongue? 
                    # dequeue AT commands only if not waiting for AT response to finish
                    # receive will take priority if you are receiving
                    # use a waitForReply.instead of the txflag, which is for the tx indictor
                    # check if there is a command
                    if not wait_for_reply and  not queue.empty(): 
                        wait_for_reply = True
                        cmd = await queue.get()
                        if cmd.startswith('SEND='):
                            # parse the command SEND=#,msglen,msg) 
                            _, _msg_len, msg = cmd.split(',', 2) # the 2 here accounts for commas in msg
                            msg_len = int(_msg_len) # _msglen is a string
                            # use insnsstr() here to avoid scrolling if 40 characters (the maximum)
                            if msg_len == 40:
                                dsply.rxinsnstr(msg, msg_len, fg_bg = dsply.YELLOW_BLACK)
                            else:
                                dsply.rxaddnstr(msg, msg_len, fg_bg = dsply.YELLOW_BLACK)

                            tx_col=0  # local transmit window cursor position
                            dsply.txwin.move(tx_row, tx_col) # cursor to tx initial input position
                            dsply.txwin.clear()
                            dsply.txwin.noutrefresh()
                            self.tx_buf_reset()

                            # flash the LoRa® indicator on transmit
                            dsply.stwin.addnstr(0,dsply.TXRX_COL, dsply.TXRX_LBL, dsply.TXRX_LEN, 
                                                cur.color_pair(dsply.WHITE_RED))
                            dsply.stwin.noutrefresh()
                            tx_flag = True # transmitting 
                            dirty = True # really True this time 
                        elif cmd.startswith('DELAY,'):
                            _,delay = cmd.split(',',1)
                            await asyncio.sleep(float(delay))
                            wait_for_reply = False # not an AT command!
                            continue # use this to escape
                        await at_cmd( cmd ) # send command to serial port to rylr998
                    continue # remember that RCV and AT cmd responses take priority

                elif ch == cur.ascii.ETX: # CTRL-C
                    cur.noraw()     # go back to cooked mode
                    cur.resetty()   # restore the terminal
                    print("\n")
                    return

                elif ch == cur.ascii.ESC: 
                    # refresh the border
                    dsply.draw_border()
                    # refresh the border

                    tx_col = 0
                    dsply.txwin.move(tx_row, tx_col)
                    self.tx_buf_reset()
                    dsply.txwin.erase()
                    dsply.txwin.noutrefresh() # may not be needed

                    dirty = True

                elif ch == cur.ascii.LF:
                    if self.tx_len > 0:
                        # the SEND_COMMAND includes the address 
                        # Don't be silly: you don't have to send only to your address!!!
                        # you could send to some other address
                        await queue.put(f"SEND={self.addr},{str(self.tx_len)},{self.tx_buf}")

                elif ch == cur.KEY_LEFT:
                    tx_col = max(0, tx_col - 1)
                    dsply.txwin.move(tx_row, tx_col)
                    dsply.txwin.noutrefresh()
                    dirty = True

                elif ch == cur.KEY_RIGHT:
                    tx_col = min(tx_col+1, self.tx_len, 39)
                    dsply.txwin.move(tx_row, tx_col)
                    dsply.txwin.noutrefresh()
                    dirty = True

                elif ch == cur.KEY_DC: # Delete
                    if tx_col >= self.tx_len:
                        continue
                    # tx_col must be to the left of a character to delete somethin  to the right
                    self.tx_buf = self.tx_buf[0:tx_col] + self.tx_buf[tx_col+1:min(40,self.tx_len)]
                    self.tx_len = max(0,min(40, self.tx_len)-1)
                    dsply.txwin.delch(tx_row,tx_col)
                    if self.tx_len < 40:
                        dsply.txwin.addnstr(tx_row, 0, self.tx_buf ,self.tx_len)
                    else:
                        dsply.txwin.insnstr(tx_row, 0, self.tx_buf, self.tx_len)
                    dsply.txwin.move(tx_row,tx_col)
                    dsply.txwin.noutrefresh()
                    dirty = True

                elif ch == cur.ascii.BS: # Backspace
                    if tx_col == 0:
                        continue # nothing to delete
                    # tx_col > 0 here: must be to the right of a character to delete something to the left
                    self.tx_buf = self.tx_buf[0:max(0,tx_col-1)]+self.tx_buf[tx_col:self.tx_len]
                    self.tx_len = len(self.tx_buf) # Don't take chances with this
                    tx_col -= 1
                    dsply.txwin.clear() # clear the transmit window
                    if self.tx_len < 40:
                        dsply.txwin.addnstr(tx_row, 0, self.tx_buf, self.tx_len) # display the tx buffer
                    else:
                        dsply.txwin.insnstr(tx_row, 0, self.tx_buf, self.tx_len)  # display the tx buffer 
                    dsply.txwin.move(tx_row, tx_col) # move the cursor
                    dsply.txwin.noutrefresh()
                    dirty = True

                elif cur.ascii.isascii(ch):
                    if self.tx_len == 40 and tx_col < 40:
                        continue   # don't change!
                    self.tx_buf = self.tx_buf[0:tx_col] + str(chr(ch)) + self.tx_buf[tx_col:min(39,self.tx_len)]
                    self.tx_len = min(40, self.tx_len+1) #  
                    #txwin.insnstr(tx_row, tx_col, str(chr(ch)),1)
                    if self.tx_len < 40:
                        dsply.txwin.addnstr(tx_row, 0, self.tx_buf ,self.tx_len)
                    else:
                        dsply.txwin.insnstr(tx_row, 0, self.tx_buf, self.tx_len)
                    tx_col = min(39, tx_col+1)
                    dsply.txwin.move(tx_row, tx_col)
                    dsply.txwin.noutrefresh()
                    dirty = True

        except Exception as e:
            logging.error(f"Error in xcvr: {e}")
            raise
        finally:
            loop.stop()  # Stop urwid main loop before raising KeyboardInterrupt
            raise KeyboardInterrupt
 
# end of the XCVR loop

if __name__ == "__main__":
    import re # regular expressions for argument checking
    from src.ui.constants import (RadioDefaults, RadioLimits)
    from src.config.validators import (
        bandcheck, pwrcheck, modecheck, netidcheck, uartcheck,
         paramcheck, validate_netid_parameter
    )

 
    # Get args from new parser
    from src.config.parser import parse_args
    args = parse_args()
    
    # Apply all validation functions to the args
    args.band = bandcheck(args.band)
    if args.pwr is not None:
        args.pwr = pwrcheck(args.pwr)
    args.mode = modecheck(args.mode)  
    args.netid = netidcheck(args.netid)
    args.port = uartcheck(args.port)

     # Parameter validation including netid check
    validate_netid_parameter(args.netid, args.parameter)
    args.parameter = paramcheck(args.parameter)

    rylr  = RYLR998(args)
    try:
        asyncio.run(cur.wrapper(rylr.xcvr))
    except KeyboardInterrupt:
        pass
    finally:
        print("73!")