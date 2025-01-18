#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
import time
from src.ui.windows.receive_window import ReceiveWindow
from src.ui.constants import ColorPair, WindowDimensions, WindowPosition

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
    height, width = 28, 42  # Original window dimensions
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
        receive._scroll_if_needed()
        receive.window.addstr(receive.row, 0, "Basic window test")
        receive._advance_row()
        receive.window.noutrefresh()
        curses.doupdate()
        time.sleep(1)

        # Test scroll helper methods
        for i in range(WindowDimensions.RECEIVE_HEIGHT - 2):  # Leave room for final message
            receive._scroll_if_needed()
            receive.window.addstr(receive.row, 0, f"Test line {i}")
            
            receive._advance_row()
            receive.window.noutrefresh()
            curses.doupdate()
            time.sleep(0.2)

        # Final message
        receive._scroll_if_needed()
        receive.window.addstr(receive.row, 0, "Press any key to exit")
        receive._advance_row()
        receive.window.noutrefresh()
        curses.doupdate()

    try:
        run_test()
        stdscr.getch()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        curses.wrapper(test_receive_window)
    except Exception as e:
        print(f"Error: {e}")