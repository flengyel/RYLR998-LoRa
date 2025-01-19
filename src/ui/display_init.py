#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""
Display initialization for the RYLR998 LoRa terminal interface.
Handles curses setup, color initialization, and window creation.

This module initializes the display components:
- Border window (main container)
- Status window (radio parameters and indicators)
- Receive window (message display)
- Transmit window (user input)

All windows are created with proper dimensions and positions based on
constants defined in src.ui.constants.
"""

import curses
import curses.ascii
import locale
from typing import Tuple
import logging
from contextlib import contextmanager

from src.ui.windows.status_window import StatusWindow
from src.ui.windows.receive_window import ReceiveWindow
from src.ui.windows.transmit_window import TransmitWindow
from src.ui.constants import ColorPair, WindowDimensions, BorderPos

# Ensure proper locale for curses
locale.setlocale(locale.LC_ALL, '')

class DisplayInitError(Exception):
    """Raised when display initialization fails"""
    pass

@contextmanager
def safe_curses_init():
    """Context manager for safe curses initialization and cleanup"""
    try:
        yield
    except curses.error as e:
        raise DisplayInitError(f"Curses initialization failed: {str(e)}")
    except Exception as e:
        raise DisplayInitError(f"Display initialization failed: {str(e)}")

def check_terminal_size(stdscr) -> None:
    """
    Verify terminal meets minimum size requirements.
    
    Args:
        stdscr: Standard screen from curses
        
    Raises:
        DisplayInitError: If terminal is too small
    """
    max_y, max_x = stdscr.getmaxyx()
    height, width = WindowDimensions.MAX_ROW, WindowDimensions.MAX_COL
    
    if max_y < height or max_x < width:
        raise DisplayInitError(
            f"Terminal too small. Needs at least {width}x{height}, "
            f"got {max_x}x{max_y}"
        )

def initialize_colors() -> None:
    """
    Initialize color pairs for the display.
    
    Raises:
        DisplayInitError: If color initialization fails
    """
    try:
        curses.start_color()
        curses.use_default_colors()
        
        # Initialize base colors
        curses.init_color(curses.COLOR_RED, 1000, 0, 0)
        curses.init_color(curses.COLOR_GREEN, 0, 1000, 0)
        curses.init_color(curses.COLOR_BLUE, 0, 0, 1000)
        
        # Initialize color pairs
        curses.init_pair(ColorPair.YELLOW_BLACK.value, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.GREEN_BLACK.value, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.BLUE_BLACK.value, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.RED_BLACK.value, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.BLACK_PINK.value, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.WHITE_RED.value, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(ColorPair.WHITE_GREEN.value, curses.COLOR_WHITE, curses.COLOR_GREEN)
    except curses.error as e:
        raise DisplayInitError(f"Color initialization failed: {str(e)}")

def create_border_window(height: int, width: int) -> curses.window:
    """
    Create and initialize the border window.
    
    Args:
        height: Window height
        width: Window width
        
    Returns:
        curses.window: Initialized border window
        
    Raises:
        DisplayInitError: If window creation fails
    """
    try:
        border_win = curses.newwin(height, width, 0, 0)
        border_win.border()
        
        # Draw horizontal lines for status area
        for y in [BorderPos.RX_ST_DIV, BorderPos.ST_TX_DIV]:
            border_win.addch(y, 0, curses.ACS_LTEE)
            border_win.hline(y, 1, curses.ACS_HLINE, width-2)
            border_win.addch(y, width-1, curses.ACS_RTEE)
        
        border_win.noutrefresh()
        return border_win
    except curses.error as e:
        raise DisplayInitError(f"Border window creation failed: {str(e)}")

def initialize_display(stdscr) -> Tuple[curses.window, StatusWindow, ReceiveWindow, TransmitWindow]:
    """
    Initialize the complete display system.
    
    Args:
        stdscr: Standard screen from curses
        
    Returns:
        Tuple containing:
        - border_win: Main border window
        - status: Status window instance
        - receive: Receive window instance
        - transmit: Transmit window instance
        
    Raises:
        DisplayInitError: If any part of initialization fails
    """
    with safe_curses_init():
        # Check terminal size first
        check_terminal_size(stdscr)
        
        # Initialize colors
        initialize_colors()
        
        # Create main border window
        border_win = create_border_window(
            WindowDimensions.MAX_ROW,
            WindowDimensions.MAX_COL
        )
        
        try:
            # Create component windows
            status = StatusWindow(border_win)
            receive = ReceiveWindow(border_win)
            transmit = TransmitWindow(border_win)
            
            return border_win, status, receive, transmit
            
        except Exception as e:
            logging.error(f"Window component initialization failed: {str(e)}")
            raise DisplayInitError(f"Window component initialization failed: {str(e)}")
