#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
import time
from src.ui.constants import ColorPair
from src.ui.windows.status_window import StatusWindow
from src.ui.windows.receive_window import ReceiveWindow
from src.ui.windows.transmit_window import TransmitWindow

def test_basic_window(stdscr):
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

    def run_test():
        # Create main border window
        border_win = curses.newwin(28, 42, 0, 0)
        border_win.border()
        
        # Draw horizontal lines for status area
        for y in [21, 23]:
            border_win.addch(y, 0, curses.ACS_LTEE)
            border_win.hline(y, 1, curses.ACS_HLINE, 40)
            border_win.addch(y, 41, curses.ACS_RTEE)
        
        border_win.refresh()

        # Create all windows using their classes
        receive = ReceiveWindow(border_win)
        status = StatusWindow(border_win)
        transmit = TransmitWindow(border_win)

        # Test each window
        receive.add_line("Testing receive window...")
        curses.doupdate()
        time.sleep(1)

        status.update_lora_status(ColorPair.WHITE_GREEN)
        curses.doupdate()
        time.sleep(1)

        transmit.add_char(ord('T'))
        transmit.add_char(ord('e'))
        transmit.add_char(ord('s'))
        transmit.add_char(ord('t'))
        curses.doupdate()
        time.sleep(1)

        # Exit countdown in receive window
        for i in range(3):
            receive.add_line(f"Exiting in {3-i} seconds")
            curses.doupdate()
            time.sleep(1)

    try:
        run_test()
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    try:
        curses.wrapper(test_basic_window)
    except Exception as e:
        print(f"Error: {e}")

