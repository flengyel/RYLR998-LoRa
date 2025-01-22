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
            WindowSize.RX_HEIGHT,
            WindowSize.RX_WIDTH,
            WindowPosition.RX_START_ROW,
            WindowPosition.RX_START_COL
        )
        self.window.scrollok(True)
        self.window.bkgd(' ', curses.color_pair(ColorPair.YELLOW_BLACK.value))
        self.row = 0
        self.col = 0
        self.max_row = WindowSize.RX_HEIGHT - 1

    def _scroll_if_needed(self):
        """Scroll window if at maximum row"""
        if self.row > self.max_row:
            self.window.scroll()
            self.row = self.max_row
            return True
        return False

    def add_line(self, msg: str, fg_bg: int = ColorPair.BLUE_BLACK.value):
        """
        Add a line of text with length control and color.
        Uses insnstr for max-length lines to prevent scrolling,
        addnstr otherwise.
        
        Args:
            msg: String to display
            fg_bg: Color pair to use (default BLUE_BLACK)
        """
        msglen = len(msg)
        self._scroll_if_needed()
        
        # Use insnstr if exactly at max length to prevent scrolling
        if msglen == WindowSize.MAX_MSG_LEN:
            self.window.insnstr(self.row, self.col, msg, WindowSize.MAX_MSG_LEN, 
                              curses.color_pair(fg_bg))
        else:
            self.window.addnstr(self.row, self.col, msg, WindowSize.MAX_MSG_LEN, 
                              curses.color_pair(fg_bg))
        
        self.row += 1
        self.window.noutrefresh()