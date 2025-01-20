#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
import time
from src.ui.display_init import initialize_display
from src.ui.constants import WindowSize, ColorPair

def test_status_window(stdscr):
    """Test the status window functionality"""
    # Get terminal size
    max_y, max_x = stdscr.getmaxyx()
    height, width = WindowSize.MAX_ROW, WindowSize.MAX_COL
    if max_y < height or max_x < width:
        raise curses.error(f"Terminal too small. Needs at least {width}x{height}, got {max_x}x{max_y}")

    def run_test():
        # Initialize all windows using display_init
        _, status, receive, _ = initialize_display(stdscr)
        
        # Test LoRa indicator colors
        receive.add_line("Testing LoRa indicator...")
        status.update_lora_status(ColorPair.WHITE_BLACK)
        curses.doupdate()
        time.sleep(1)
        
        receive.add_line("Testing receive indicator (green)")
        status.update_lora_status(ColorPair.WHITE_GREEN)
        curses.doupdate()
        time.sleep(1)
        
        receive.add_line("Testing transmit indicator (red)")
        status.update_lora_status(ColorPair.WHITE_RED)
        curses.doupdate()
        time.sleep(1)

        # Test value updates
        receive.add_line("Testing radio parameters...")
        status.update_vfo("915000000")
        status.update_power("22")
        status.update_netid("18")
        curses.doupdate()
        time.sleep(1)

        status.update_lora_status(ColorPair.WHITE_BLACK)  # Reset LoRa indicator
        curses.doupdate()

        # Exit countdown
        for i in range(3):
            receive.add_line(f"Exiting in {3-i} seconds")
            curses.doupdate()
            time.sleep(1)

    try:
        run_test()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        curses.wrapper(test_status_window)
    except Exception as e:
        print(f"Error: {e}")