#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
import time
from src.ui.windows.status_window import StatusWindow
from src.ui.constants import ColorPair, WindowSize, WindowPosition

class TestReceiveWindow:
    """Simple receive window just for test messages"""
    def __init__(self, parent_window):
        self.window = parent_window.derwin(
            WindowSize.RECEIVE_HEIGHT,
            WindowSize.RECEIVE_WIDTH,
            WindowPosition.RX_START_ROW,
            WindowPosition.RX_START_COL
        )
        self.window.scrollok(True)
        self.row = 0
        
    def add_message(self, msg: str):
        """Add a message to the receive window"""
        if self.row >= WindowSize.RECEIVE_HEIGHT:
            self.window.scroll()
            self.row = WindowSize.RECEIVE_HEIGHT - 1
            
        self.window.addstr(self.row, 0, msg)
        self.row += 1
        self.window.noutrefresh()

def test_status_window(stdscr):
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

    # Create windows
    receive = TestReceiveWindow(border_win)
    status = StatusWindow(border_win)
    
    def run_test():
        # Test LoRa indicator colors
        receive.add_message("Testing LoRa indicator...")
        status.update_lora_status(ColorPair.WHITE_BLACK)
        curses.doupdate()
        time.sleep(1)
        
        receive.add_message("Testing receive indicator (green)")
        status.update_lora_status(ColorPair.WHITE_GREEN)
        curses.doupdate()
        time.sleep(1)
        
        receive.add_message("Testing transmit indicator (red)")
        status.update_lora_status(ColorPair.WHITE_RED)
        curses.doupdate()
        time.sleep(1)

        # Test value updates
        receive.add_message("Testing radio parameters...")
        status.update_vfo("915000000")
        status.update_power("22")
        status.update_netid("18")
        curses.doupdate()
        time.sleep(1)

        status.update_lora_status(ColorPair.WHITE_BLACK)  # Reset LoRa indicator
        curses.doupdate()

        for i in range(3):
            receive.add_message(f"Exiting in {3-i} seconds")
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

