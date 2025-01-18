#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
from src.ui.constants import (
    ColorPair, WindowDimensions, WindowPosition
)

class ReceiveWindow:
    """Handles the message receive/display area"""
    def __init__(self, parent_window):
        """Create receive window at the specified position in parent window"""
        self.window = parent_window.derwin(
            WindowDimensions.RECEIVE_HEIGHT,
            WindowDimensions.RECEIVE_WIDTH,
            WindowPosition.RX_START_ROW,
            WindowPosition.RX_START_COL
        )
        self.window.scrollok(True)
        self.window.bkgd(' ', curses.color_pair(ColorPair.YELLOW_BLACK.value))
        self.row = 0
        self.col = 0
        self.max_row = WindowDimensions.RECEIVE_HEIGHT - 1

    def _scroll_if_needed(self):
        """Scroll window if at maximum row"""
        if self.row == self.max_row:
            self.window.scroll()
            
    def _advance_row(self):
        """Move to next row, handling scrolling"""
        self.row = min(self.max_row, self.row + 1)
        self.col = 0
        