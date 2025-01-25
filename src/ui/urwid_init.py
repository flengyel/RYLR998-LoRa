#!/usr/bin/env python3
# -*- coding: utf8 -*-

import urwid
from src.ui.constants import (
    WindowSize, StatusLabels, WindowPosition, ColorPair, BorderPos, RadioDefaults
)

def create_frame():
    """Create the main application frame with three panels"""
    
    # Create receive area
    receive_content = urwid.Text("Receive Area")
    receive_area = urwid.Filler(receive_content, 'top', top=WindowPosition.RX_START_ROW)
    
    # Status window with two rows
   # Status window with two rows and dividers
# Status window with two rows and dividers
    status_content = urwid.Pile([
        # Top row with vertical dividers
        urwid.Columns([
            ('fixed', StatusLabels.TXRX_LEN, urwid.Text(StatusLabels.TXRX_LABEL)),
            ('fixed', 1, urwid.Text('│')),  # Vertical divider
            ('fixed', StatusLabels.ADDR_LEN + 8, urwid.Text(StatusLabels.ADDR_LABEL)),
            ('fixed', 1, urwid.Text('│')),  # Vertical divider
            ('fixed', StatusLabels.RSSI_LEN + 8, urwid.Text(StatusLabels.RSSI_LABEL)),
            ('fixed', 1, urwid.Text('│')),  # Vertical divider
            ('fixed', StatusLabels.SNR_LEN + 5, urwid.Text(StatusLabels.SNR_LABEL))
        ]),
        urwid.Divider('─'),  # Horizontal divider
        # Bottom row with vertical dividers
        urwid.Columns([
            ('fixed', StatusLabels.STATUS_ROW2_VFO, 
                urwid.Text(f"VFO {RadioDefaults.FREQ}")),
            ('fixed', 1, urwid.Text('│')),  # Vertical divider
            ('fixed', StatusLabels.STATUS_ROW2_PWR,
                urwid.Text(f"PWR {RadioDefaults.POWER}")),
            ('fixed', 1, urwid.Text('│')),  # Vertical divider
            ('fixed', StatusLabels.STATUS_ROW2_NETID,
                urwid.Text(f"NETWORK ID {RadioDefaults.NETID}"))
        ])
    ])
    # Add Filler for vertical alignment
    status_area = urwid.Filler(status_content, 'middle')
    
    # Use double-line box drawing characters for the outer box
    status_box = urwid.LineBox(
        status_area,
        title="Status",
        tline='═',  # Double line for top
        bline='═',  # Double line for bottom
        lline='║',  # Double line for left
        rline='║',  # Double line for right
        tlcorner='╔',  # Top left corner
        trcorner='╗',  # Top right corner
        blcorner='╚',  # Bottom left corner
        brcorner='╝'   # Bottom right corner
    )
    
    # Transmit area
    transmit_edit = urwid.Edit("")
    transmit_area = urwid.Filler(transmit_edit)

    # Create the main pile with fixed dimensions from WindowSize
    main_pile = urwid.Pile([
        ('fixed', WindowSize.RX_HEIGHT, urwid.LineBox(receive_area, title="Messages")),
        ('fixed', WindowSize.ST_HEIGHT, status_box),  # Use the new status_box here
        ('fixed', WindowSize.TX_HEIGHT, urwid.LineBox(transmit_area, title="Transmit"))
    ])

    # Wrap pile in Columns for fixed width from WindowSize
    main_cols = urwid.Columns([
        ('fixed', WindowSize.MAX_COL, main_pile)
    ])

    # Create final frame with fixed dimensions
    frame = urwid.Frame(
        body=main_cols,
        header=None,
        footer=None,
        focus_part='body'
    )

    return frame

def initialize_display(event_loop):
    """Initialize the urwid display with our frame"""
    
    # Define color palette based on ColorPair enum
    palette = [
        ('default',    'light gray', 'black'),
        ('status',     'white',      'dark blue'),
        ('receive',    'light cyan', 'black'),
        ('transmit',   'yellow',     'black'),
        ('border',     'white',      'black'),
        ('lora_tx',    'white',      'dark red'),
        ('lora_rx',    'white',      'dark green')
    ]

    # Create frame with fixed dimensions
    frame = create_frame()
    
    # Handle input (temporary)
    def handle_input(key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        return True

    # Initialize the screen and handle unsupported color depths
    screen = urwid.raw_display.Screen()
    
    try:
        screen.set_terminal_properties(colors=256)
    except KeyError as e:
        print(f"Unsupported terminal color depth. Using default colors: {e}")

    main_loop = urwid.MainLoop(
        widget=frame,
        palette=palette,
        event_loop=event_loop,
        unhandled_input=handle_input,
        screen=screen
    )

    return main_loop