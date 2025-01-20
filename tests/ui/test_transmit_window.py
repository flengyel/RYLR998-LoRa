#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
import time
from src.ui.display_init import initialize_display
from src.ui.constants import WindowSize

def test_transmit_window(stdscr):
    """Test the transmit window functionality"""
    # Get terminal size
    max_y, max_x = stdscr.getmaxyx()
    height, width = WindowSize.MAX_ROW, WindowSize.MAX_COL
    if max_y < height or max_x < width:
        raise curses.error(f"Terminal too small. Needs at least {width}x{height}, got {max_x}x{max_y}")

    def run_test():
        # Initialize using display_init
        _, _, receive, transmit = initialize_display(stdscr)
        
        # Test basic input
        receive.add_line("Testing basic input...")
        test_text = "Hello, World!"
        for ch in test_text:
            transmit.add_char(ord(ch))
            curses.doupdate()
            time.sleep(0.1)
        
        time.sleep(1)
        receive.add_line("Testing cursor movement...")
        for _ in range(5):  # Move left 5 times
            transmit.move_cursor(curses.KEY_LEFT)
            curses.doupdate()
            time.sleep(0.2)
        
        for _ in range(3):  # Move right 3 times
            transmit.move_cursor(curses.KEY_RIGHT)
            curses.doupdate()
            time.sleep(0.2)
            
        time.sleep(1)
        receive.add_line("Testing delete...")
        transmit.delete_char()
        curses.doupdate()
        time.sleep(1)
        
        receive.add_line("Testing backspace...")
        transmit.backspace()
        curses.doupdate()
        time.sleep(1)
        
        receive.add_line("Testing clear line...")
        time.sleep(1)
        transmit.clear_line()
        curses.doupdate()
        time.sleep(1)
        
        # Test 40 character limit
        receive.add_line("Testing 40 character limit...")
        test_text = "1234567890" * 5  # 50 characters, should stop at 40
        for ch in test_text:
            transmit.add_char(ord(ch))
            curses.doupdate()
            time.sleep(0.05)
        time.sleep(1)

        # Edge case tests
        receive.add_line("Testing move right at edge")
        transmit.move_cursor(curses.KEY_RIGHT)
        curses.doupdate()
        time.sleep(1)

        # Move left 
        receive.add_line("Go left and insert an X")
        transmit.move_cursor(curses.KEY_LEFT)
        curses.doupdate()
        time.sleep(0.05)

        receive.add_line(f"col: {transmit.col} buffer len {transmit.buffer_len}") 
        curses.doupdate()
        time.sleep(1)

        transmit.add_char(ord('X'))
        curses.doupdate() 
        receive.add_line("Stuck huh? Delete first")
        transmit.delete_char()
        time.sleep(1)

        receive.add_line("now add an 'X'")
        transmit.add_char(ord('X'))
        curses.doupdate()
        time.sleep(1)

        receive.add_line(f"col: {transmit.col} buffer len {transmit.buffer_len}") 
        curses.doupdate()
        time.sleep(1)

        # Additional edge case tests
        receive.add_line("Testing rapid input at buffer boundary")
        transmit.clear_line()
        test_text = "1234567890" * 4  # Fill to 40 chars
        for ch in test_text:
            transmit.add_char(ord(ch))
            curses.doupdate()
        
        # Try rapid adds at boundary
        for ch in "ABC":  # Should not add any of these
            transmit.add_char(ord(ch))
            curses.doupdate()
        receive.add_line(f"Buffer length after overflow attempt: {transmit.buffer_len}")
        time.sleep(1)

        # Test cursor movement and insert
        receive.add_line("Move to start and try insertions")
        for _ in range(40):  # Move to start
            transmit.move_cursor(curses.KEY_LEFT)
        receive.add_line(f"Cursor at: {transmit.col}")
        transmit.add_char(ord('X'))  # Should insert
        receive.add_line(f"Buffer length after insert: {transmit.buffer_len}")
        time.sleep(1)

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
        curses.wrapper(test_transmit_window)
    except Exception as e:
        print(f"Error: {e}")