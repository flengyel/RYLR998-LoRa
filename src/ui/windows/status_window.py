#!/usr/bin/env python3
# -*- coding: utf8 -*-

import curses as cur
from src.ui.constants import ColorPair, StatusLabels, WindowPosition

class StatusWindow:
    """Handles the status display area"""
    def __init__(self, parent_window):
        """Create status window at the specified position in parent window"""
        # Create derwin at the correct position
        self.window = parent_window.derwin(
            WindowPosition.ST_HEIGHT,
            WindowPosition.ST_WIDTH,
            WindowPosition.ST_START_ROW,
            WindowPosition.ST_START_COL
        )
        
        # Set default background
        self.window.bkgd(' ', cur.color_pair(ColorPair.WHITE_BLACK.value))
        
        # Draw initial labels
        self._draw_labels()
        self.window.noutrefresh()

    def _draw_labels(self):
        """Draw all static status window labels"""
        self.window.addnstr(
            StatusLabels.TXRX_ROW, 
            StatusLabels.TXRX_COL,
            StatusLabels.TXRX_LABEL,
            StatusLabels.TXRX_LEN,
            cur.color_pair(ColorPair.WHITE_BLACK.value)
        )
        
        self.window.addnstr(
            StatusLabels.ADDR_ROW,
            StatusLabels.ADDR_COL,
            StatusLabels.ADDR_LABEL,
            StatusLabels.ADDR_LEN,
            cur.color_pair(ColorPair.WHITE_BLACK.value)
        )
        
        self.window.addnstr(
            StatusLabels.RSSI_ROW,
            StatusLabels.RSSI_COL,
            StatusLabels.RSSI_LABEL,
            StatusLabels.RSSI_LEN,
            cur.color_pair(ColorPair.WHITE_BLACK.value)
        )
        
        self.window.addnstr(
            StatusLabels.SNR_ROW,
            StatusLabels.SNR_COL,
            StatusLabels.SNR_LABEL,
            StatusLabels.SNR_LEN,
            cur.color_pair(ColorPair.WHITE_BLACK.value)
        )
        
        self.window.addnstr(
            StatusLabels.VFO_ROW,
            StatusLabels.VFO_COL,
            StatusLabels.VFO_LABEL,
            StatusLabels.VFO_LEN,
            cur.color_pair(ColorPair.WHITE_BLACK.value)
        )
        
        self.window.addnstr(
            StatusLabels.PWR_ROW,
            StatusLabels.PWR_COL,
            StatusLabels.PWR_LABEL,
            StatusLabels.PWR_LEN,
            cur.color_pair(ColorPair.WHITE_BLACK.value)
        )
        
        self.window.addnstr(
            StatusLabels.NETID_ROW,
            StatusLabels.NETID_COL,
            StatusLabels.NETID_LABEL,
            StatusLabels.NETID_LEN,
            cur.color_pair(ColorPair.WHITE_BLACK.value)
        )

    def update_lora_status(self, color_pair: ColorPair):
        """Update LoRa indicator color"""
        self.window.addnstr(
            StatusLabels.TXRX_ROW,
            StatusLabels.TXRX_COL,
            StatusLabels.TXRX_LABEL,
            StatusLabels.TXRX_LEN,
            cur.color_pair(color_pair.value)
        )
        self.window.noutrefresh()

    def update_addr(self, addr: str):
        """Update address display"""
        self.window.addstr(
            StatusLabels.ADDR_ROW,
            StatusLabels.ADDR_VAL_COL,
            addr,
            cur.color_pair(ColorPair.BLUE_BLACK.value)
        )
        self.window.noutrefresh()

    def update_rssi(self, rssi: str):
        """Update RSSI value"""
        self.window.addstr(
            StatusLabels.RSSI_ROW,
            StatusLabels.RSSI_VAL_COL,
            rssi,
            cur.color_pair(ColorPair.BLUE_BLACK.value)
        )
        self.window.noutrefresh()

    def update_snr(self, snr: str):
        """Update SNR value"""
        self.window.addstr(
            StatusLabels.SNR_ROW,
            StatusLabels.SNR_VAL_COL,
            snr,
            cur.color_pair(ColorPair.BLUE_BLACK.value)
        )
        self.window.noutrefresh()

    def update_vfo(self, freq: str):
        """Update VFO frequency"""
        self.window.addstr(
            StatusLabels.VFO_ROW,
            StatusLabels.VFO_VAL_COL,
            freq,
            cur.color_pair(ColorPair.WHITE_BLACK.value)
        )
        self.window.noutrefresh()

    def update_power(self, pwr: str):
        """Update power setting"""
        self.window.addstr(
            StatusLabels.PWR_ROW,
            StatusLabels.PWR_VAL_COL,
            pwr,
            cur.color_pair(ColorPair.WHITE_BLACK.value)
        )
        self.window.noutrefresh()

    def update_netid(self, netid: str):
        """Update network ID"""
        self.window.addstr(
            StatusLabels.NETID_ROW,
            StatusLabels.NETID_VAL_COL,
            netid,
            cur.color_pair(ColorPair.WHITE_BLACK.value)
        )
        self.window.noutrefresh()

# Example usage in xcvr():
"""
# Initialize
status_window = StatusWindow(border_window)

# When receiving:
status_window.update_lora_status(ColorPair.WHITE_GREEN)
status_window.update_addr(addr)
status_window.update_rssi(rssi)
status_window.update_snr(snr)

# When transmitting:
status_window.update_lora_status(ColorPair.WHITE_RED)

# When setting parameters:
status_window.update_vfo(freq)
status_window.update_power(pwr)
status_window.update_netid(netid)
"""
