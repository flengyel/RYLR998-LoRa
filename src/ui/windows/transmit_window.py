#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
import curses.ascii
from src.ui.constants import (
    ColorPair, WindowSize, WindowPosition
)

class TransmitWindow:
    """Handles text input and display"""
    def __init__(self, parent_window):
        self.window = parent_window.derwin(
            WindowSize.TRANSMIT_HEIGHT,
            WindowSize.TRANSMIT_WIDTH,
            WindowPosition.TX_START_ROW,
            WindowPosition.TX_START_COL
        )
        
        self.window.nodelay(True)
        self.window.keypad(True)
        self.window.notimeout(False)
        self.window.bkgd(' ', curses.color_pair(ColorPair.YELLOW_BLACK.value))
        
        self.row = 0
        self.col = 0
        self.buffer = ''
        self.buffer_len = 0

    def get_input(self) -> int:
        return self.window.getch()

    def clear_line(self):
        self.window.erase()
        self.col = 0
        self.buffer = ''
        self.buffer_len = 0
        self.window.move(self.row, self.col)
        self.window.noutrefresh()

    def move_cursor(self, direction: int):
        if direction == curses.KEY_LEFT:
            self.col = max(0, self.col - 1)
        elif direction == curses.KEY_RIGHT:
            self.col = min(self.col + 1, self.buffer_len, 39)
        self.window.move(self.row, self.col)
        self.window.noutrefresh()

    def add_char(self, ch: int):
        if self.buffer_len >= 40:
            return
        
        self.buffer = (self.buffer[:self.col] + 
                      chr(ch) + 
                      self.buffer[self.col:])
        self.buffer_len += 1
        
        self.window.erase()
        if self.buffer_len < 40:
            self.window.addstr(self.row, 0, self.buffer)
        else:
            self.window.insnstr(self.row, 0, self.buffer, 40)
        self.col = min(39, self.col + 1)
        self.window.move(self.row, self.col)
        self.window.noutrefresh()

    def delete_char(self):
        if self.col >= self.buffer_len:
            return
            
        self.buffer = self.buffer[:self.col] + self.buffer[self.col+1:]
        self.buffer_len -= 1  # Can't go below 0 since we checked col < buffer_len
        
        self.window.erase()
        if self.buffer_len < 40:
            self.window.addstr(self.row, 0, self.buffer)
        else:
            self.window.insnstr(self.row, 0, self.buffer, 40)
        self.window.move(self.row, self.col)
        self.window.noutrefresh()

    def backspace(self):
        if self.col <= 0:  # Changed from > 0 to <= 0 for clarity
            return
            
        self.buffer = self.buffer[:self.col-1] + self.buffer[self.col:]
        self.buffer_len -= 1
        self.col -= 1  # Col was > 0 so this is safe
        
        self.window.erase()
        if self.buffer_len < 40:
            self.window.addstr(self.row, 0, self.buffer)
        else:
            self.window.insnstr(self.row, 0, self.buffer, 40)
        self.window.move(self.row, self.col)
        self.window.noutrefresh()

    def get_buffer(self) -> str:
        return self.buffer

    def get_buffer_length(self) -> int:
        return self.buffer_len

