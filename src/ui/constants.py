#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses as cur
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
    MAX_ROW: Final[int] = 28
    MAX_COL: Final[int] = 42
    TX_ROW: Final[int] = 26    # Transmit window row
    RX_ROWS: Final[int] = 20   # Number of rows in receive window
    ST_ROWS: Final[int] = 3    # Number of rows in status window
    TX_ROWS: Final[int] = 1    # Number of rows in transmit window
    MAX_MSG_LEN: Final[int] = 40  # Maximum message length

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
    ADDR_VAL_COL: Final[int] = 13  # Where address value starts

    # RSSI
    RSSI_LABEL: Final[str] = "RSSI"
    RSSI_LEN: Final[int] = 4
    RSSI_ROW: Final[int] = 0
    RSSI_COL: Final[int] = 21
    RSSI_VAL_COL: Final[int] = 26  # Where RSSI value starts

    # SNR
    SNR_LABEL: Final[str] = "SNR"
    SNR_LEN: Final[int] = 3
    SNR_ROW: Final[int] = 0
    SNR_COL: Final[int] = 32
    SNR_VAL_COL: Final[int] = 36   # Where SNR value starts

    # VFO
    VFO_LABEL: Final[str] = "VFO"
    VFO_LEN: Final[int] = 3
    VFO_ROW: Final[int] = 2
    VFO_COL: Final[int] = 1
    VFO_VAL_COL: Final[int] = 5    # Where frequency value starts

    # Power
    PWR_LABEL: Final[str] = "PWR"
    PWR_LEN: Final[int] = 3
    PWR_ROW: Final[int] = 2
    PWR_COL: Final[int] = 17
    PWR_VAL_COL: Final[int] = 21   # Where power value starts

    # Network ID
    NETID_LABEL: Final[str] = "NETWORK ID"
    NETID_LEN: Final[int] = 10
    NETID_ROW: Final[int] = 2
    NETID_COL: Final[int] = 26
    NETID_VAL_COL: Final[int] = 37  # Where network ID value starts

@dataclass(frozen=True)
class WindowPosition:
    """Window positions relative to parent window"""
    # Receive window
    RX_START_ROW: Final[int] = 1
    RX_START_COL: Final[int] = 1
    RX_HEIGHT: Final[int] = 20
    RX_WIDTH: Final[int] = 40

    # Status window
    ST_START_ROW: Final[int] = 22
    ST_START_COL: Final[int] = 1
    ST_HEIGHT: Final[int] = 3
    ST_WIDTH: Final[int] = 40

    # Transmit window
    TX_START_ROW: Final[int] = 26
    TX_START_COL: Final[int] = 1
    TX_HEIGHT: Final[int] = 1
    TX_WIDTH: Final[int] = 40

class TerminalModes:
    """Terminal mode settings"""
    RAW_MODE: Final[bool] = True          # "Raw, almost vegan" character handling
    NODELAY_MODE: Final[bool] = True      # Non-blocking input
    KEYPAD_MODE: Final[bool] = True       # Special key handling
    NO_TIMEOUT_MODE: Final[bool] = False  # ESC sequence handling
    SAVE_TTY: Final[bool] = True          # Save terminal settings
    
    @classmethod
    def setup_terminal(cls, screen):
        """Apply standard terminal settings"""
        if cls.SAVE_TTY:
            cur.savetty()
        if cls.RAW_MODE:
            cur.raw()
        screen.nodelay(cls.NODELAY_MODE)

class SystemConstants:
    """System-level constants"""
    ESC_DELAY_MS: Final[int] = 1    # Escape key delay in milliseconds
    WINDOWS_CURSES: Final[bool] = cur.error == getattr(cur, 'error', None)  # Check if using windows-curses

class ColorValues:
    """Color intensity values (0-1000)"""
    MAX_INTENSITY: Final[int] = 1000
    MIN_INTENSITY: Final[int] = 0
    
    # RGB Color definitions
    RED: Final[tuple] = (MAX_INTENSITY, MIN_INTENSITY, MIN_INTENSITY)
    GREEN: Final[tuple] = (MIN_INTENSITY, MAX_INTENSITY, MIN_INTENSITY)
    BLUE: Final[tuple] = (MIN_INTENSITY, MIN_INTENSITY, MAX_INTENSITY)

class BorderChars:
    """Border drawing characters"""
    HORIZONTAL = cur.ACS_HLINE
    VERTICAL = cur.ACS_VLINE
    TOP_T = cur.ACS_TTEE
    BOTTOM_T = cur.ACS_BTEE
    LEFT_T = cur.ACS_LTEE
    RIGHT_T = cur.ACS_RTEE
    TOP_LEFT = cur.ACS_ULCORNER
    TOP_RIGHT = cur.ACS_URCORNER
    BOTTOM_LEFT = cur.ACS_LLCORNER
    BOTTOM_RIGHT = cur.ACS_LRCORNER

class ErrorMessages:
    """Error code messages"""
    ERR_1: Final[str] = "AT command missing 0x0D 0x0A."
    ERR_2: Final[str] = "AT command missing 'AT'."
    ERR_4: Final[str] = "Unknown AT command."
    ERR_5: Final[str] = "Data length specified does not match the data length."
    ERR_10: Final[str] = "Transmit time exceeds limit."
    ERR_12: Final[str] = "CRC error on receive."
    ERR_13: Final[str] = "TX data exceeds 240 bytes."
    ERR_14: Final[str] = "Failed to write flash memory."
    ERR_15: Final[str] = "Unknown failure."
    ERR_17: Final[str] = "Last TX was not completed."
    ERR_18: Final[str] = "Preamble value is not allowed."
    ERR_19: Final[str] = "RX failure. Header error."
    ERR_20: Final[str] = "Invalid time in MODE 2 setting."
    ERR_UNKNOWN: Final[str] = "Unknown error code."
    ERR_FORMAT: Final[str] = "ERR={}: {}"  # Format string for error messages

@dataclass(frozen=True)
class WindowDefaults:
    """Default window settings"""
    BACKGROUND_CHAR: Final[str] = ' '
    DEFAULT_MSG_COLOR: Final[int] = ColorPair.BLUE_BLACK.value
    RX_MAX_ROW: Final[int] = 19  # Maximum row in receive window (0-based)
    TX_MAX_COL: Final[int] = 39  # Maximum column in transmit window (0-based)

@dataclass(frozen=True)
class CursorPos:
    """Default cursor positions"""
    INITIAL_ROW: Final[int] = 0
    INITIAL_COL: Final[int] = 0

class BorderPos:
    """Border positions for window divisions"""
    # Horizontal divisions (Y coordinates)
    RX_ST_DIV: Final[int] = 21   # Between receive and status
    ST_TX_DIV: Final[int] = 23   # Between status and transmit
    TX_BOT_DIV: Final[int] = 25  # Bottom of transmit window

    # Vertical divisions (X coordinates)
    STATUS_DIV1: Final[int] = 7   # First status divider
    STATUS_DIV2: Final[int] = 20  # Second status divider
    STATUS_DIV3: Final[int] = 31  # Third status divider
    
    TX_DIV1: Final[int] = 16      # First transmit area divider
    TX_DIV2: Final[int] = 25      # Second transmit area divider
