#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
import time
from src.ui.windows.receive_window import ReceiveWindow
from src.ui.constants import ColorPair, WindowSize, WindowPosition

def test_receive_window(stdscr):
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

    # Get terminal size
    max_y, max_x = stdscr.getmaxyx()
    height, width = WindowSize.MAX_ROW, WindowSize.MAX_COL  # Original window dimensions
    if max_y < height or max_x < width:
        raise curses.error(f"Terminal too small. Needs at least {width}x{height}, got {max_x}x{max_y}")

    # Create border window
    border_win = curses.newwin(height, width, 0, 0)
    border_win.border()
    
    # Draw horizontal lines for status area
    for y in [21, 23]:
        border_win.addch(y, 0, curses.ACS_LTEE)
        border_win.hline(y, 1, curses.ACS_HLINE, width-2)
        border_win.addch(y, width-1, curses.ACS_RTEE)
    
    border_win.noutrefresh()

    # Create receive window
    receive = ReceiveWindow(border_win)
    
    def run_test():
        # Test basic window creation
        receive.add_line("Basic window test")
        curses.doupdate()
        time.sleep(1)

        # Test scroll helper methods - fill window and scroll past it
        for i in range(WindowSize.RX_HEIGHT + 5):  
            receive.add_line(f"Test line {i:2d}")
            curses.doupdate()
            time.sleep(0.2)

        time.sleep(1)  # Pause to see scrolling result


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

