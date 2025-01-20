#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
import time
from src.ui.windows.transmit_window import TransmitWindow
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

def test_transmit_window(stdscr):
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
    transmit = TransmitWindow(border_win)
    
    def run_test():
        # Test basic input
        receive.add_message("Testing basic input...")
        test_text = "Hello, World!"
        for ch in test_text:
            transmit.add_char(ord(ch))
            curses.doupdate()
            time.sleep(0.1)
        
        time.sleep(1)
        receive.add_message("Testing cursor movement...")
        for _ in range(5):  # Move left 5 times
            transmit.move_cursor(curses.KEY_LEFT)
            curses.doupdate()
            time.sleep(0.2)
        
        for _ in range(3):  # Move right 3 times
            transmit.move_cursor(curses.KEY_RIGHT)
            curses.doupdate()
            time.sleep(0.2)
            
        time.sleep(1)
        receive.add_message("Testing delete...")
        transmit.delete_char()
        curses.doupdate()
        time.sleep(1)
        
        receive.add_message("Testing backspace...")
        transmit.backspace()
        curses.doupdate()
        time.sleep(1)
        
        receive.add_message("Testing clear line...")
        time.sleep(1)
        transmit.clear_line()
        curses.doupdate()
        time.sleep(1)
        
        # Test 40 character limit
        receive.add_message("Testing 40 character limit...")
        test_text = "1234567890" * 5  # 50 characters, should stop at 40
        for ch in test_text:
            transmit.add_char(ord(ch))
            curses.doupdate()
            time.sleep(0.05)
        time.sleep(1)

        # Edge case tests
        receive.add_message("Testing move right at edge")
        transmit.move_cursor(curses.KEY_RIGHT)
        curses.doupdate()
        time.sleep(1)

        # move left 
        receive.add_message("Go left and insert an X")
        transmit.move_cursor(curses.KEY_LEFT)
        curses.doupdate()
        time.sleep(0.05)

        receive.add_message(f"col: {transmit.col} buffer len {transmit.buffer_len}") 
        curses.doupdate()
        time.sleep(1)

        transmit.add_char(ord('X'))
        curses.doupdate() 
        receive.add_message("Stuck huh? Delete first")
        transmit.delete_char()
        time.sleep(1)

        receive.add_message("now add an 'X'")
        transmit.add_char(ord('X'))
        curses.doupdate()
        time.sleep(1)

        receive.add_message(f"col: {transmit.col} buffer len {transmit.buffer_len}") 
        curses.doupdate()
        time.sleep(1)

        receive.add_message("now add a 'Y'")
        transmit.add_char(ord('Y'))
        curses.doupdate()
        time.sleep(1)

        receive.add_message("HAH! Delete needed!")
        curses.doupdate()
        time.sleep(1)

        receive.add_message(f"col: {transmit.col} buffer len {transmit.buffer_len}") 
        curses.doupdate()
        time.sleep(1)
        
        transmit.delete_char()
        transmit.add_char(ord('Y'))
        curses.doupdate()
        time.sleep(1)

        # Additional invariant tests
        receive.add_message("Testing invariants...")
        time.sleep(1)

        # Test rapid input at buffer boundary
        receive.add_message("Rapid input at buffer boundary")
        transmit.clear_line()
        test_text = "1234567890" * 4  # Fill to 40 chars
        for ch in test_text:
            transmit.add_char(ord(ch))
            curses.doupdate()
        
        # Try rapid adds at boundary
        for ch in "ABC":  # Should not add any of these
            transmit.add_char(ord(ch))
            curses.doupdate()
        receive.add_message(f"Buffer length after overflow attempt: {transmit.buffer_len}")
        time.sleep(1)

        # Test cursor movement and insert
        receive.add_message("Move to start and try insertions")
        for _ in range(40):  # Move to start
            transmit.move_cursor(curses.KEY_LEFT)
        receive.add_message(f"Cursor at: {transmit.col}")
        transmit.add_char(ord('X'))  # Should not insert
        receive.add_message(f"Buffer length after insert attempt: {transmit.buffer_len}")
        time.sleep(1)

        # Test multiple deletes
        receive.add_message("Multiple delete test")
        for _ in range(5):
            transmit.delete_char()
            curses.doupdate()
            time.sleep(0.1)
        receive.add_message(f"Buffer length after deletes: {transmit.buffer_len}")
        time.sleep(1)

        # Test boundary cursor movement
        receive.add_message("Testing cursor boundaries")
        for _ in range(45):  # Try to move past right edge
            transmit.move_cursor(curses.KEY_RIGHT)
        receive.add_message(f"Cursor after right moves: {transmit.col}")
        for _ in range(45):  # Try to move past left edge
            transmit.move_cursor(curses.KEY_LEFT)
        receive.add_message(f"Cursor after left moves: {transmit.col}")
        time.sleep(1)

        # Test inserting while moving left
        receive.add_message("Testing insert while moving left")
        transmit.clear_line()
        # First fill to almost full
        test_text = "1234567890" * 3 + "12345"  # 35 characters
        for ch in test_text:
            transmit.add_char(ord(ch))
            curses.doupdate()
        receive.add_message(f"Initial buffer length: {transmit.buffer_len}")
        
        # Move left and insert
        for _ in range(10):  # Move left 10 positions
            transmit.move_cursor(curses.KEY_LEFT)
        receive.add_message(f"Cursor position after left: {transmit.col}")
        
        # Should be able to insert until buffer_len hits 40
        test_text = "ABCDE"  # These should all insert
        for ch in test_text:
            transmit.add_char(ord(ch))
            curses.doupdate()
            time.sleep(0.1)
            receive.add_message(f"After insert '{ch}': col={transmit.col} len={transmit.buffer_len}")
        time.sleep(1)

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
        curses.wrapper(test_transmit_window)
    except Exception as e:
        print(f"Error: {e}")

