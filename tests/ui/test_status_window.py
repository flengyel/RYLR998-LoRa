#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
import time
from src.ui.windows.status_window import StatusWindow
from src.ui.constants import ColorPair

def test_status_window(stdscr):
    # Initialize color pairs
    curses.start_color()
    curses.use_default_colors()
    
    curses.init_color(curses.COLOR_RED, 1000, 0, 0)
    curses.init_color(curses.COLOR_GREEN, 0, 1000, 0)
    curses.init_color(curses.COLOR_BLUE, 0, 0, 1000)
    
    # Initialize all the color pairs
    curses.init_pair(ColorPair.YELLOW_BLACK.value, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(ColorPair.GREEN_BLACK.value, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(ColorPair.BLUE_BLACK.value, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(ColorPair.RED_BLACK.value, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(ColorPair.BLACK_PINK.value, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(ColorPair.WHITE_RED.value, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(ColorPair.WHITE_GREEN.value, curses.COLOR_WHITE, curses.COLOR_GREEN)

    # Create a border window (parent window for status)
    height, width = 28, 42  # Original window dimensions
    border_win = stdscr.derwin(height, width, 0, 0)
    border_win.border()
    
    # Create horizontal lines for status area
    for y in [21, 23]:
        border_win.addch(y, 0, curses.ACS_LTEE)
        border_win.hline(y, 1, curses.ACS_HLINE, width-2)
        border_win.addch(y, width-1, curses.ACS_RTEE)
    
    border_win.noutrefresh()

    # Create status window
    status = StatusWindow(border_win)
    
    # Test sequence
    def run_test():
        # Test LoRa indicator colors
        print("Testing LoRa indicator...")
        status.update_lora_status(ColorPair.WHITE_BLACK)
        curses.doupdate()
        time.sleep(1)
        
        status.update_lora_status(ColorPair.WHITE_GREEN)  # Receive
        curses.doupdate()
        time.sleep(1)
        
        status.update_lora_status(ColorPair.WHITE_RED)    # Transmit
        curses.doupdate()
        time.sleep(1)

        # Test value updates
        print("Testing value updates...")
        status.update_addr("1234")
        status.update_rssi("-120")
        status.update_snr("5.2")
        curses.doupdate()
        time.sleep(2)

        status.update_vfo("915000000")
        status.update_power("22")
        status.update_netid("18")
        curses.doupdate()
        time.sleep(2)

    try:
        run_test()
        print("Press any key to exit...")
        stdscr.getch()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    print("Starting status window test...")
    curses.wrapper(test_status_window)
    print("Test complete.")
