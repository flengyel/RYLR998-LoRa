#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
import time
from src.ui.display_init import initialize_display
from src.ui.constants import WindowSize, ColorPair

def test_window_interaction(stdscr):
    """Test interaction between transmit, receive and status windows"""
    # Check terminal size
    max_y, max_x = stdscr.getmaxyx()
    height, width = WindowSize.MAX_ROW, WindowSize.MAX_COL
    if max_y < height or max_x < width:
        raise curses.error(f"Terminal too small. Needs at least {width}x{height}, got {max_x}x{max_y}")

    def run_test():
        # Initialize all windows
        border_win, status, receive, transmit = initialize_display(stdscr)

        # Set initial LoRa status to GREEN
        receive.add_line("Setting initial LoRa status to GREEN...")
        status.update_lora_status(ColorPair.WHITE_GREEN)
        curses.doupdate()
        time.sleep(1)

        # Enter test message
        test_msg = "Test transmission sequence"
        receive.add_line("Entering test message...")
        for ch in test_msg:
            transmit.add_char(ord(ch))
            curses.doupdate()
            time.sleep(0.1)
        time.sleep(1)

        # Save transmit buffer state
        buffer_content = transmit.get_buffer()
        buffer_length = transmit.get_buffer_length()
        receive.add_line(f"Buffer contains: '{buffer_content}' ({buffer_length} chars)")
        curses.doupdate()
        time.sleep(1)

        # Simulate transmission
        receive.add_line("Simulating transmission...")
        
        # Flash LoRa status RED
        status.update_lora_status(ColorPair.WHITE_RED)
        curses.doupdate()
        time.sleep(1)

        # Show transmitted message in receive window
        receive.add_line(buffer_content, fg_bg=ColorPair.YELLOW_BLACK)
        curses.doupdate()
        time.sleep(1)

        # Clear transmit window and buffer
        transmit.clear_line()
        curses.doupdate()
        time.sleep(1)

        # Verify transmit buffer is cleared
        new_buffer = transmit.get_buffer()
        new_length = transmit.get_buffer_length()
        receive.add_line(f"New buffer state: '{new_buffer}' ({new_length} chars)")
        curses.doupdate()
        time.sleep(1)

        # Restore LoRa status to GREEN
        status.update_lora_status(ColorPair.WHITE_GREEN)
        curses.doupdate()
        time.sleep(1)

        # Test complete
        receive.add_line("Test sequence complete")
        curses.doupdate()
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
        curses.wrapper(test_window_interaction)
    except Exception as e:
        print(f"Error: {e}")
