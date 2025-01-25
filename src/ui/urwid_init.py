#!/usr/bin/env python3
# -*- coding: utf8 -*-

import urwid
from src.ui.constants import (
    WindowSize, StatusLabels, WindowPosition, ColorPair
)

def create_frame():
    """Create the main application frame with three panels"""
    
    # Create receive area
    receive_content = urwid.Text("Receive Area")
    receive_area = urwid.Filler(receive_content, 'top', top=WindowPosition.RX_START_ROW)
    
    # Status window with two rows
    status_content = urwid.Pile([
        # Top row with indicators
        urwid.Columns([
            ('fixed', StatusLabels.TXRX_LEN, urwid.Text(StatusLabels.TXRX_LABEL)),
            ('fixed', StatusLabels.ADDR_LEN + StatusLabels.ADDR_VAL_COL - StatusLabels.ADDR_COL,
                urwid.Text(StatusLabels.ADDR_LABEL)),
            ('fixed', StatusLabels.RSSI_LEN + StatusLabels.RSSI_VAL_COL - StatusLabels.RSSI_COL,
                urwid.Text(StatusLabels.RSSI_LABEL)),
            ('fixed', StatusLabels.SNR_LEN + StatusLabels.SNR_VAL_COL - StatusLabels.SNR_COL,
                urwid.Text(StatusLabels.SNR_LABEL)),
        ]),
        # Bottom row with values
        urwid.Columns([
            ('fixed', StatusLabels.VFO_LEN + StatusLabels.VFO_VAL_COL - StatusLabels.VFO_COL,
                urwid.Text(StatusLabels.VFO_LABEL)),
            ('fixed', StatusLabels.PWR_LEN + StatusLabels.PWR_VAL_COL - StatusLabels.PWR_COL,
                urwid.Text(StatusLabels.PWR_LABEL)),
            ('fixed', StatusLabels.NETID_LEN + StatusLabels.NETID_VAL_COL - StatusLabels.NETID_COL,
                urwid.Text(StatusLabels.NETID_LABEL))
        ])
    ])
    status_area = urwid.Filler(status_content)
    
    # Transmit area
    transmit_edit = urwid.Edit("")
    transmit_area = urwid.Filler(transmit_edit)

    # Create the main pile with fixed dimensions from WindowSize
    main_pile = urwid.Pile([
        ('fixed', WindowSize.RX_HEIGHT, urwid.LineBox(receive_area, title="Messages")),
        ('fixed', WindowSize.ST_HEIGHT, urwid.LineBox(status_area, title="Status")),
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