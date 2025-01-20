#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
from typing import Tuple

from src.ui.constants import ColorPair, WindowDimensions, BorderPos
from src.ui.windows.status_window import StatusWindow
from src.ui.windows.receive_window import ReceiveWindow
from src.ui.windows.transmit_window import TransmitWindow

class DisplayInitError(Exception):
    """Raised when display initialization fails"""
    pass

def initialize_display(stdscr) -> Tuple[curses.window, StatusWindow, ReceiveWindow, TransmitWindow]:
    """Initialize the display system using the proven window setup"""
    try:
        # Initialize color pairs
        curses.start_color()
        curses.use_default_colors()

        curses.init_color(curses.COLOR_RED, 1000, 0, 0)
        curses.init_color(curses.COLOR_GREEN, 0, 1000, 0)
        curses.init_color(curses.COLOR_BLUE, 0, 0, 1000)

        curses.init_pair(ColorPair.YELLOW_BLACK.value, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.GREEN_BLACK.value, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.BLUE_BLACK.value, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.RED_BLACK.value, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.BLACK_PINK.value, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(ColorPair.WHITE_RED.value, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(ColorPair.WHITE_GREEN.value, curses.COLOR_WHITE, curses.COLOR_GREEN)

        # Create main border window
        border_win = curses.newwin(WindowDimensions.MAX_ROW, WindowDimensions.MAX_COL, 0, 0)
        border_win.border()
        
        # Draw horizontal lines for status area
        for y in [BorderPos.RX_ST_DIV, BorderPos.ST_TX_DIV]:
            border_win.addch(y, 0, curses.ACS_LTEE)
            border_win.hline(y, 1, curses.ACS_HLINE, WindowDimensions.MAX_COL-2)
            border_win.addch(y, WindowDimensions.MAX_COL-1, curses.ACS_RTEE)
        
        border_win.refresh()

        # Create window objects
        receive = ReceiveWindow(border_win)
        status = StatusWindow(border_win)
        transmit = TransmitWindow(border_win)

        return border_win, status, receive, transmit

    except curses.error as e:
        raise DisplayInitError(f"Failed to initialize display: {e}")
    except Exception as e:
        raise DisplayInitError(f"Unexpected error during display initialization: {e}")

