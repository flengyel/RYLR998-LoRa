#!/usr/bin/env python3
# -*- coding: utf8 -*-

import urwid
from src.ui.constants import WindowSize

def create_frame():
    """Create the main application frame with three panels"""
    
    # Create placeholder widgets
    receive_content = urwid.Text("Receive Area")
    receive_area = urwid.Filler(receive_content, 'top', top=1)
    
    status_content = urwid.Columns([
        ('fixed', 6, urwid.Text("LoRa")),
        ('fixed', 12, urwid.Text("ADDR")),
        ('fixed', 10, urwid.Text("RSSI")),
        ('fixed', 8, urwid.Text("SNR")),
    ])
    status_area = urwid.Filler(status_content)
    
    transmit_edit = urwid.Edit("")
    transmit_area = urwid.Filler(transmit_edit)

    # Create the main pile with fixed dimensions
    main_pile = urwid.Pile([
        ('fixed', WindowSize.RX_HEIGHT, urwid.LineBox(receive_area, title="Messages")),
        ('fixed', WindowSize.ST_HEIGHT, urwid.LineBox(status_area, title="Status")),
        ('fixed', WindowSize.TX_HEIGHT, urwid.LineBox(transmit_area, title="Transmit"))
    ])

    # Wrap pile in Columns for fixed width
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
    
    # Define color palette
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

    # Create MainLoop with explicit screen size
    screen = urwid.raw_display.Screen()
    screen.set_terminal_properties(WindowSize.MAX_COL)
    
    main_loop = urwid.MainLoop(
        widget=frame,
        palette=palette,
        event_loop=event_loop,
        unhandled_input=handle_input,
        screen=screen
    )

    return main_loop

def create_placeholder_widgets():
    """Create placeholder widgets for development/testing"""
    receive = urwid.Text("Receive Area\n" * 3)
    status = urwid.Text("Status Area")
    transmit = urwid.Edit("") 
    return receive, status, transmit

