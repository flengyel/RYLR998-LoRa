#!/usr/bin/env python3
# -*- coding: utf8 -*-
import curses
from dataclasses import dataclass
from enum import Enum
from typing import Final

class ColorPair(Enum):
    """Color pair definitions for the display"""
    WHITE_BLACK = 0    # Built in, cannot change
    YELLOW_BLACK = 1   # User text
    GREEN_BLACK = 2    # Status indicator (our palette is off, bear with me)
    BLUE_BLACK = 3     # Status indicator
    RED_BLACK = 4      # Errors
    BLACK_PINK = 5     # Received text (really magenta on black)
    WHITE_RED = 6      # Transmit indicator
    WHITE_GREEN = 7    # Receive indicator

@dataclass(frozen=True)
class Timing:
    """Timing constants"""
    ONE_SEC: Final[float] = 1.0
    HALF_SEC: Final[float] = 0.5
    FOURTH_SEC: Final[float] = 0.25
    TENTH_SEC: Final[float] = 0.1
    CENTI_SEC: Final[float] = 0.01

@dataclass(frozen=True)
class WindowSize:
    """Window dimensions"""
    # Main window dimensions
    MAX_ROW: Final[int] = 28
    MAX_COL: Final[int] = 42
    
    # Component window dimensions
    RX_ROWS: Final[int] = 20
    RX_WIDTH: Final[int] = 40
    
    ST_ROWS: Final[int] = 3
    ST_WIDTH: Final[int] = 40
    
    TX_ROW: Final[int] = 26
    TX_ROWS: Final[int] = 1
    TX_WIDTH: Final[int] = 40
    
    MAX_MSG_LEN: Final[int] = 40

@dataclass(frozen=True)
class StatusLabels:
    """Status window label definitions"""
    # LoRa Status
    TXRX_LABEL: Final[str] = " LoRa "
    TXRX_LEN: Final[int] = 6
    TXRX_ROW: Final[int] = 0
    TXRX_COL: Final[int] = 0

    # Address
    ADDR_LABEL: Final[str] = "ADDR"
    ADDR_LEN: Final[int] = 4
    ADDR_ROW: Final[int] = 0
    ADDR_COL: Final[int] = 8
    ADDR_VAL_COL: Final[int] = 13

    # RSSI
    RSSI_LABEL: Final[str] = "RSSI"
    RSSI_LEN: Final[int] = 4
    RSSI_ROW: Final[int] = 0
    RSSI_COL: Final[int] = 21
    RSSI_VAL_COL: Final[int] = 26

    # SNR
    SNR_LABEL: Final[str] = "SNR"
    SNR_LEN: Final[int] = 3
    SNR_ROW: Final[int] = 0
    SNR_COL: Final[int] = 32
    SNR_VAL_COL: Final[int] = 36

    # VFO
    VFO_LABEL: Final[str] = "VFO"
    VFO_LEN: Final[int] = 3
    VFO_ROW: Final[int] = 2
    VFO_COL: Final[int] = 1
    VFO_VAL_COL: Final[int] = 5

    # Power
    PWR_LABEL: Final[str] = "PWR"
    PWR_LEN: Final[int] = 3
    PWR_ROW: Final[int] = 2
    PWR_COL: Final[int] = 17
    PWR_VAL_COL: Final[int] = 21

    # Network ID
    NETID_LABEL: Final[str] = "NETWORK ID"
    NETID_LEN: Final[int] = 10
    NETID_ROW: Final[int] = 2
    NETID_COL: Final[int] = 26
    NETID_VAL_COL: Final[int] = 37

@dataclass(frozen=True)
class WindowPosition:
    """Window positions relative to parent"""
    RX_START_ROW: Final[int] = 1
    RX_START_COL: Final[int] = 1
    ST_START_ROW: Final[int] = 22
    ST_START_COL: Final[int] = 1
    TX_START_ROW: Final[int] = 26
    TX_START_COL: Final[int] = 1

@dataclass(frozen=True)
class BorderPos:
    """Border positions"""
    RX_ST_DIV: Final[int] = 21   # Between receive and status
    ST_TX_DIV: Final[int] = 23   # Between status and transmit
    TX_BOT_DIV: Final[int] = 25  # Bottom of transmit window
    STATUS_DIV1: Final[int] = 7   # First status divider
    STATUS_DIV2: Final[int] = 20  # Second status divider
    STATUS_DIV3: Final[int] = 31  # Third status divider
    
    TX_DIV1: Final[int] = 16     # First transmit divider
    TX_DIV2: Final[int] = 25     # Second transmit divider

class BorderChars:
    """Border drawing characters - access only after curses initialization"""
    @staticmethod
    def get_chars():
        return {
            'HORIZONTAL': curses.ACS_HLINE,
            'VERTICAL': curses.ACS_VLINE,
            'TOP_T': curses.ACS_TTEE,
            'BOTTOM_T': curses.ACS_BTEE,
            'LEFT_T': curses.ACS_LTEE,
            'RIGHT_T': curses.ACS_RTEE,
            'TOP_LEFT': curses.ACS_ULCORNER,
            'TOP_RIGHT': curses.ACS_URCORNER,
            'BOTTOM_LEFT': curses.ACS_LLCORNER,
            'BOTTOM_RIGHT': curses.ACS_LRCORNER
        }
