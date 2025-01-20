#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
import time
from src.ui.display_init import initialize_display
from src.ui.constants import WindowSize

def test_receive_window(stdscr):
    """Test the receive window functionality"""
    # Get terminal size
    max_y, max_x = stdscr.getmaxyx()
    height, width = WindowSize.MAX_ROW, WindowSize.MAX_COL
    if max_y < height or max_x < width:
        raise curses.error(f"Terminal too small. Needs at least {width}x{height}, got {max_x}x{max_y}")

    def run_test():
        # Initialize using display_init
        _, _, receive, _ = initialize_display(stdscr)
        
        # Test basic window creation
        receive.add_line("Basic window test")
        curses.doupdate()
        time.sleep(1)

        # Test scroll functionality - fill window and scroll past it
        for i in range(WindowSize.RX_HEIGHT + 5):  
            receive.add_line(f"Test line {i:2d}")
            curses.doupdate()
            time.sleep(0.2)

        time.sleep(1)  # Pause to see scrolling result

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
        curses.wrapper(test_receive_window)
    except Exception as e:
        print(f"Error: {e}")