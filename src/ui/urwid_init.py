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
    status_content = urwid.Pile([
        # Top row - status indicators with dividers
        urwid.Columns([
            ('fixed', BorderPos.STATUS_DIV1, 
                urwid.Columns([
                    ('fixed', StatusLabels.TXRX_LEN, urwid.Text(StatusLabels.TXRX_LABEL))
                ])
            ),
            ('fixed', BorderPos.STATUS_DIV2 - BorderPos.STATUS_DIV1,
                urwid.Text(StatusLabels.ADDR_LABEL)
            ),
            ('fixed', BorderPos.STATUS_DIV3 - BorderPos.STATUS_DIV2,
                urwid.Text(StatusLabels.RSSI_LABEL)
            ),
            ('fixed', WindowSize.ST_WIDTH - BorderPos.STATUS_DIV3,
                urwid.Text(StatusLabels.SNR_LABEL)
            )
        ]),
        urwid.Divider('─'),  # Horizontal divider between rows
        # Bottom row - VFO/PWR/NETWORK ID
        urwid.Columns([
            ('fixed', StatusLabels.STATUS_ROW2_VFO,
                urwid.Text(StatusLabels.VFO_FULL_LABEL.format(RadioDefaults.FREQ))
            ),
            ('fixed', StatusLabels.STATUS_ROW2_PWR,
                urwid.Text(StatusLabels.PWR_FULL_LABEL.format(RadioDefaults.POWER))
            ),
            ('fixed', StatusLabels.STATUS_ROW2_NETID,
                urwid.Text(StatusLabels.NETID_FULL_LABEL.format(RadioDefaults.NETID))
            )
        ])
    ])
    status_area = urwid.Filler(status_content)

    status_box = urwid.LineBox(
        status_area,
        title="Status",
        tline='─', 
        bline='─',
        lline='│',
        rline='│',
        tlcorner='┌',
        trcorner='┐',
        blcorner='└',
        brcorner='┘'
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