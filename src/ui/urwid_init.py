#!/usr/bin/env python3
# -*- coding: utf8 -*-

import urwid
from src.ui.constants import WindowSize

def create_frame():
    """Create the main application frame with three panels"""
    # Create placeholder widgets
    receive_area = urwid.Filler(urwid.Text("Receive Area"))
    status_area = urwid.Text("Status Area")
    transmit_area = urwid.Edit("") 

    # Create the layout
    layout = urwid.Pile([
        # Receive window takes most space
        ('weight', WindowSize.RX_HEIGHT, urwid.LineBox(receive_area, title="Messages")),
        # Status area is fixed height
        ('fixed', WindowSize.ST_HEIGHT, urwid.LineBox(status_area, title="Status")),
        # Transmit area is fixed height
        ('fixed', WindowSize.TX_HEIGHT, urwid.LineBox(transmit_area, title="Transmit"))
    ])

    # Create the main frame
    frame = urwid.Frame(
        body=layout,
        header=None,
        footer=None,
        focus_part='body'
    )

    # Force minimum window size using BoxAdapter
    frame = urwid.BoxAdapter(frame, WindowSize.MAX_ROW)
    frame = urwid.Padding(frame, 'center', WindowSize.MAX_COL)

    return frame

def initialize_display(event_loop):
    """Initialize the urwid display with our frame"""
    # Create basic color palette
    palette = [
        ('default', 'light gray', 'black'),
        ('status', 'white', 'dark blue'),
        ('receive', 'light cyan', 'black'),
        ('transmit', 'yellow', 'black'),
        ('border', 'white', 'black')
    ]

    # Create the main frame
    frame = create_frame()

    # Create and return the MainLoop
    main_loop = urwid.MainLoop(
        frame,
        palette=palette,
        event_loop=event_loop,
        unhandled_input=lambda key: key == 'q'  # Temporary exit on 'q'
    )

    return main_loop
