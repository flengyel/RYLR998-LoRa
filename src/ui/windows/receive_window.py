#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
from src.ui.constants import (
    ColorPair, WindowSize, WindowPosition
)

class ReceiveWindow:
    """Handles the message receive/display area"""
    def __init__(self, parent_window):
        self.window = parent_window.derwin(
            WindowSize.RECEIVE_HEIGHT,
            WindowSize.RECEIVE_WIDTH,
            WindowPosition.RX_START_ROW,
            WindowPosition.RX_START_COL
        )
        self.window.scrollok(True)
        self.window.bkgd(' ', curses.color_pair(ColorPair.YELLOW_BLACK.value))
        self.row = 0
        self.col = 0
        self.max_row = WindowSize.RECEIVE_HEIGHT - 1

    def _scroll_if_needed(self):
        """Scroll window if at maximum row"""
        if self.row > self.max_row:  # Changed from >= to >
            self.window.scroll()
            self.row = self.max_row
            return True
        return False


    def add_line(self, msg: str):
        """Add a line of text, always checking scroll"""
        self._scroll_if_needed()  # Always check scroll first
        self.window.addstr(self.row, self.col, msg)
        self.row += 1
        self.window.noutrefresh()

