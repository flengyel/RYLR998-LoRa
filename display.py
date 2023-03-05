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
# This is the Display class

import curses as cur
import _curses
import curses.ascii

#import datetime
import locale
locale.setlocale(locale.LC_ALL, '')
#stdscr.addstr(0, 0, mystring.encode('UTF-8'))


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

    MAX_ROW   = 28
    MAX_COL   = 42

    # this needs to be part of the Display class
    rxrow = 0   # rxwin_y relative window coordinates
    rxcol = 0   # rxwin_x
    maxrow =  MAX_ROW
    maxcol =  MAX_COL
    bdrwin = None # the outer window.
    rxwin = None  # receive window
    txwin = None # transmit window
    stwin = None # status window

    # receive and transmit window border initialization

    # The next two inner functions restrict access to the receive 
    # and transmit window border variables rxbdr and txbdr, resp., 
    # and return the derived receive and transmit windows 
    # rxwin and txwin, respectively.

    # Relative coordinates are congenial - might remove magic numbers

    def derive_bdrwin(self, scr:_curses) -> None:
        bdrwin = scr.derwin(self.maxrow,self.maxcol,0,0)
        self.bdrwin = bdrwin


    def draw_border(self) -> None:
        # define the border in one place. Program from outer to inner.
        self.bdrwin.border()
        # Fill in the details

        # receive window border
        self.bdrwin.addch(21,0, cur.ACS_LTEE)
        self.bdrwin.hline(21,1,cur.ACS_HLINE,self.maxcol-2)
        self.bdrwin.addch(21,self.maxcol-1, cur.ACS_RTEE)

        # status window border 
        # second line
        self.bdrwin.addch(23,0, cur.ACS_LTEE)
        self.bdrwin.hline(23,1,cur.ACS_HLINE,self.maxcol-2)
        self.bdrwin.addch(23,self.maxcol-1, cur.ACS_RTEE)

        # transmit window border
        # third line
        self.bdrwin.addch(25, 0, cur.ACS_LTEE)
        self.bdrwin.hline(25, 1, cur.ACS_HLINE,self.maxcol-2)
        self.bdrwin.addch(25, self.maxcol-1, cur.ACS_RTEE)

        # status labels
        fg_bg = cur.color_pair(self.WHITE_BLACK)
        self.bdrwin.addnstr(22, self.TXRX_COL+1, self.TXRX_LBL, self.TXRX_LEN, fg_bg) 
        self.bdrwin.addch(21, 7, cur.ACS_TTEE)
        self.bdrwin.vline(22, 7, cur.ACS_VLINE, 1,  fg_bg)
        self.bdrwin.addch(23, 7, cur.ACS_BTEE)

        self.bdrwin.addnstr(22, self.ADDR_COL+1, self.ADDR_LBL, self.ADDR_COL, fg_bg) 
        self.bdrwin.addch(21, 20, cur.ACS_TTEE)
        self.bdrwin.vline(22, 20, cur.ACS_VLINE, 1, fg_bg)
        self.bdrwin.addch(23, 20, cur.ACS_BTEE)

        self.bdrwin.addnstr(22, self.RSSI_COL+1, self.RSSI_LBL, self.RSSI_LEN, fg_bg)
        self.bdrwin.addch(21, 31, cur.ACS_TTEE)
        self.bdrwin.vline(22, 31, cur.ACS_VLINE, 1, fg_bg)
        self.bdrwin.addch(23, 31, cur.ACS_BTEE)

        self.bdrwin.addnstr(22, self.SNR_COL+1, self.SNR_LBL, self.SNR_LEN, fg_bg)

        self.bdrwin.addnstr(24, self.VFO_COL+1, self.VFO_LBL, self.VFO_LEN, fg_bg)
        self.bdrwin.addch(23, 16, cur.ACS_TTEE)
        self.bdrwin.addch(24, 16, cur.ACS_VLINE)
        self.bdrwin.addch(25, 16, cur.ACS_BTEE)

        self.bdrwin.addnstr(24, self.PWR_COL+1, self.PWR_LBL, self.PWR_LEN, fg_bg)
        self.bdrwin.addch(23, 25, cur.ACS_TTEE)
        self.bdrwin.addch(24, 25, cur.ACS_VLINE)
        self.bdrwin.addch(25, 25, cur.ACS_BTEE)

        self.bdrwin.addnstr(24, self.NETID_COL+1, self.NETID_LBL, self.NETID_LEN, fg_bg)

        self.bdrwin.noutrefresh()


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
        txwin = self.bdrwin.derwin(1,self.maxcol-2,26,1)
        self.txwin = txwin 
        # transmit window initialization
        txwin.nodelay(True)
        txwin.keypad(True)

        # I'd prefer not timing out ESC, but there is no choice. 
        txwin.notimeout(False) 

        txwin.bkgd(' ', cur.color_pair(self.YELLOW_BLACK))
        txwin.noutrefresh()


    # status "window" setup
    def derive_stwin(self) -> None:
        stwin = self.bdrwin.derwin(3,self.maxcol-2,22,1)
        self.stwin = stwin
        fg_bg = cur.color_pair(self.WHITE_BLACK)
        self.stwin.bkgd(' ', fg_bg)
        self.stwin.noutrefresh()

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

        self.derive_bdrwin(scr)
        self.draw_border()
        self.derive_rxwin()
        self.derive_stwin()
        self.derive_txwin()

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
        
