#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses
from src.ui.constants import (
    ColorPair, StatusLabels, WindowPosition, BorderChars, WindowSize
)

class StatusWindow:
    """Handles the status display area"""
    def __init__(self, parent_window):
        """Create status window at the specified position in parent window"""
        # derwin parameters: nlines (height), ncols (width), begin_y, begin_x
        self.window = parent_window.derwin(
            WindowSize.ST_HEIGHT, # height
            WindowSize.ST_WIDTH,  # width
            WindowPosition.ST_START_ROW,    # begin_y (WindowPosition.ST_START_ROW)
            WindowPosition.ST_START_COL     # begin_x (WindowPosition.ST_START_COL)
        )
        
        # Set default background
        self.window.bkgd(' ', curses.color_pair(ColorPair.WHITE_BLACK.value))
        
        # Draw initial labels
        self._draw_labels()
        self.window.noutrefresh()

    def _draw_labels(self):
        """Draw all static status window labels"""
        def add_label(row, col, text, length):
            try:
                self.window.addnstr(row, col, text, length,
                                  curses.color_pair(ColorPair.WHITE_BLACK.value))
            except curses.error as e:
                print(f"Error adding label at ({row}, {col}): {e}")
                raise
        
        # Add all status labels
        add_label(
            StatusLabels.TXRX_ROW,
            StatusLabels.TXRX_COL,
            StatusLabels.TXRX_LABEL,
            StatusLabels.TXRX_LEN
        )
        
        add_label(
            StatusLabels.ADDR_ROW,
            StatusLabels.ADDR_COL,
            StatusLabels.ADDR_LABEL,
            StatusLabels.ADDR_LEN
        )
        
        add_label(
            StatusLabels.RSSI_ROW,
            StatusLabels.RSSI_COL,
            StatusLabels.RSSI_LABEL,
            StatusLabels.RSSI_LEN
        )
        
        add_label(
            StatusLabels.SNR_ROW,
            StatusLabels.SNR_COL,
            StatusLabels.SNR_LABEL,
            StatusLabels.SNR_LEN
        )
        
        add_label(
            StatusLabels.VFO_ROW,
            StatusLabels.VFO_COL,
            StatusLabels.VFO_LABEL,
            StatusLabels.VFO_LEN
        )
        
        add_label(
            StatusLabels.PWR_ROW,
            StatusLabels.PWR_COL,
            StatusLabels.PWR_LABEL,
            StatusLabels.PWR_LEN
        )
        
        add_label(
            StatusLabels.NETID_ROW,
            StatusLabels.NETID_COL,
            StatusLabels.NETID_LABEL,
            StatusLabels.NETID_LEN
        )

    def update_lora_status(self, color_pair: ColorPair):
        """Update LoRa indicator color"""
        self.window.addnstr(
            StatusLabels.TXRX_ROW,
            StatusLabels.TXRX_COL,
            StatusLabels.TXRX_LABEL,
            StatusLabels.TXRX_LEN,
            curses.color_pair(color_pair.value)
        )
        self.window.noutrefresh()

    def update_addr(self, addr: str):
        """Update address display"""
        self.window.addstr(
            StatusLabels.ADDR_ROW,
            StatusLabels.ADDR_VAL_COL,
            addr,
            curses.color_pair(ColorPair.BLUE_BLACK.value)
        )
        self.window.noutrefresh()

    def update_rssi(self, rssi: str):
        """Update RSSI value"""
        self.window.addstr(
            StatusLabels.RSSI_ROW,
            StatusLabels.RSSI_VAL_COL,
            rssi,
            curses.color_pair(ColorPair.BLUE_BLACK.value)
        )
        self.window.noutrefresh()

    def update_snr(self, snr: str):
        """Update SNR value"""
        self.window.addstr(
            StatusLabels.SNR_ROW,
            StatusLabels.SNR_VAL_COL,
            snr,
            curses.color_pair(ColorPair.BLUE_BLACK.value)
        )
        self.window.noutrefresh()

    def update_vfo(self, freq: str):
        """Update VFO frequency"""
        self.window.addstr(
            StatusLabels.VFO_ROW,
            StatusLabels.VFO_VAL_COL,
            freq,
            curses.color_pair(ColorPair.WHITE_BLACK.value)
        )
        self.window.noutrefresh()

    def update_power(self, pwr: str):
        """Update power setting"""
        self.window.addstr(
            StatusLabels.PWR_ROW,
            StatusLabels.PWR_VAL_COL,
            pwr,
            curses.color_pair(ColorPair.WHITE_BLACK.value)
        )
        self.window.noutrefresh()

    def update_netid(self, netid: str):
        """Update network ID"""
        self.window.addstr(
            StatusLabels.NETID_ROW,
            StatusLabels.NETID_VAL_COL,
            netid,
            curses.color_pair(ColorPair.WHITE_BLACK.value)
        )
        self.window.noutrefresh()


