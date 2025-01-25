#!/usr/bin/env python3
# -*- coding: utf8 -*-
import curses
from dataclasses import dataclass
from enum import Enum
from typing import Final

@dataclass(frozen=True)
class RadioLimits:
    """RYLR998 Radio parameter limits"""
    MIN_ADDR: Final[int] = 0
    MAX_ADDR: Final[int] = 65535
    MIN_FREQ: Final[int] = 902250000
    MAX_FREQ: Final[int] = 927750000
    MIN_POWER: Final[int] = 0
    MAX_POWER: Final[int] = 22
    MIN_MODE_DELAY: Final[int] = 30
    MAX_MODE_DELAY: Final[int] = 60000
    MIN_NETID: Final[int] = 3
    MAX_NETID: Final[int] = 15
    ALT_NETID: Final[int] = 18
    MIN_SF: Final[int] = 7
    MAX_SF: Final[int] = 11
    MIN_BW: Final[int] = 7
    MAX_BW: Final[int] = 9
    MIN_CR: Final[int] = 1
    MAX_CR: Final[int] = 4
    MIN_PREAMBLE: Final[int] = 4
    MAX_PREAMBLE: Final[int] = 25
    DEFAULT_PREAMBLE: Final[int] = 12

@dataclass(frozen=True)
class WindowSize:
    """Window dimensions"""
    # Main window dimensions
    MAX_ROW: Final[int] = 28
    MAX_COL: Final[int] = 42
    
    # Receive window dimensions
    RX_HEIGHT: Final[int] = 20
    RX_WIDTH: Final[int] = 40
    
    # Status window dimensions
    ST_HEIGHT: Final[int] = 4  # Two content rows plus borders
    ST_WIDTH: Final[int] = 40
    
    # Transmit window dimensions
    TX_HEIGHT: Final[int] = 1
    TX_WIDTH: Final[int] = 40
    
    # Maximum message length
    MAX_MSG_LEN: Final[int] = 40

@dataclass(frozen=True)
class StatusLabels:
    """Status window label definitions"""
    # Row 1: Main status indicators
    TXRX_LABEL: Final[str] = " LoRa "
    TXRX_LEN: Final[int] = 6
    TXRX_COL: Final[int] = 0

    ADDR_LABEL: Final[str] = "ADDR"
    ADDR_LEN: Final[int] = 4
    ADDR_COL: Final[int] = 8
    ADDR_VAL_COL: Final[int] = 13

    RSSI_LABEL: Final[str] = "RSSI"
    RSSI_LEN: Final[int] = 4
    RSSI_COL: Final[int] = 21
    RSSI_VAL_COL: Final[int] = 26

    SNR_LABEL: Final[str] = "SNR"
    SNR_LEN: Final[int] = 3
    SNR_COL: Final[int] = 32
    SNR_VAL_COL: Final[int] = 36

    # Row 2: Settings display and formats
    STATUS_ROW2_VFO: Final[int] = 20    # Space for "VFO 915000000"
    STATUS_ROW2_PWR: Final[int] = 8     # Space for "PWR 22"
    STATUS_ROW2_NETID: Final[int] = 12  # Space for "NETWORK ID 18"
    
    VFO_FULL_LABEL: Final[str] = "VFO {}"       # For formatting with frequency
    PWR_FULL_LABEL: Final[str] = "PWR {}"       # For formatting with power
    NETID_FULL_LABEL: Final[str] = "NETWORK ID {}"  # For formatting with network ID

    # Row 2 widths and positions
    VFO_LABEL: Final[str] = "VFO"
    VFO_LEN: Final[int] = 3
    VFO_COL: Final[int] = 0
    VFO_VAL_COL: Final[int] = 4
    VFO_TOTAL_WIDTH: Final[int] = 20  # Accommodate "VFO 915000000"

    PWR_LABEL: Final[str] = "PWR"
    PWR_LEN: Final[int] = 3
    PWR_COL: Final[int] = 21
    PWR_VAL_COL: Final[int] = 25
    PWR_TOTAL_WIDTH: Final[int] = 8  # Accommodate "PWR 22"

    NETID_LABEL: Final[str] = "NETWORK ID"
    NETID_LEN: Final[int] = 10
    NETID_COL: Final[int] = 30
    NETID_VAL_COL: Final[int] = 35
    NETID_TOTAL_WIDTH: Final[int] = 12  # Accommodate "NETWORK ID 18"

@dataclass(frozen=True)
class WindowPosition:
    """Window positions relative to parent"""
    RX_START_ROW: Final[int] = 1
    RX_START_COL: Final[int] = 1
    ST_START_ROW: Final[int] = 22
    ST_START_COL: Final[int] = 1
    TX_START_ROW: Final[int] = 26
    TX_START_COL: Final[int] = 1

class ColorPair(Enum):
    """Color pair definitions"""
    WHITE_BLACK = 0
    YELLOW_BLACK = 1
    GREEN_BLACK = 2
    BLUE_BLACK = 3
    RED_BLACK = 4
    BLACK_PINK = 5
    WHITE_RED = 6
    WHITE_GREEN = 7

@dataclass(frozen=True)
class Timing:
    """Timing constants"""
    ONE_SEC: Final[float] = 1.0
    HALF_SEC: Final[float] = 0.5
    FOURTH_SEC: Final[float] = 0.25
    TENTH_SEC: Final[float] = 0.1
    CENTI_SEC: Final[float] = 0.01


@dataclass(frozen=True)
class RadioDefaults:
    """RYLR998 Radio default parameter values"""
    ADDR: Final[int] = 0
    FREQ: Final[str] = '915000000'
    POWER: Final[str] = '22'
    MODE: Final[str] = '0'
    NETID: Final[str] = '18'
    SF: Final[str] = '9'      # Spreading factor
    BW: Final[str] = '7'      # Bandwidth (7=125kHz, 8=250kHz, 9=500kHz)
    CR: Final[str] = '1'      # Coding rate
    PREAMBLE: Final[str] = '12'

@dataclass(frozen=True)
class SerialDefaults:
    """Serial port default values and options"""
    PORT: Final[str] = '/dev/ttyS0'
    BAUD: Final[str] = '115200'
    VALID_BAUDRATES: Final[tuple] = (
        '300', '1200', '4800', '9600', '19200', 
        '28800', '38400', '57600', '115200'
    )


   

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
