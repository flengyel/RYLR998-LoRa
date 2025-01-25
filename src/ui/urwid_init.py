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
    receive_box = urwid.LineBox(
        receive_area,
        title="Messages",
        tline='═',
        bline='═',
        lline='║',
        rline='║',
        tlcorner='╔',
        trcorner='╗',
        blcorner='╚',
        brcorner='╝'
    )
    
    # Status window with proper layout
    status_row1 = urwid.Columns([
        ('fixed', 6, urwid.Text("LoRa")),
        ('fixed', 1, urwid.Text("│")),
        ('fixed', 11, urwid.Text("ADDR")),
        ('fixed', 1, urwid.Text("│")),
        ('fixed', 10, urwid.Text("RSSI")),
        ('fixed', 1, urwid.Text("│")),
        ('fixed', 8, urwid.Text("SNR"))
    ])

    divider = urwid.Divider('─')

    status_row2 = urwid.Columns([
        ('fixed', 18, urwid.Text("915000000")),
        ('fixed', 7, urwid.Text("22")),
        ('fixed', 13, urwid.Text("18"))
    ])

    status_pile = urwid.Pile([
        status_row1,
        divider,
        status_row2
    ])

    status_box = urwid.LineBox(
        urwid.Filler(status_pile, 'middle'),
        title="Status",
        tline='═',
        bline='═',
        lline='║',
        rline='║',
        tlcorner='╔',
        trcorner='╗',
        blcorner='╚',
        brcorner='╝'
    )
    
    # Transmit area
    transmit_edit = urwid.Edit("")
    transmit_area = urwid.Filler(transmit_edit)
    transmit_box = urwid.LineBox(
        transmit_area,
        title="Transmit",
        tline='═',
        bline='═',
        lline='║',
        rline='║',
        tlcorner='╔',
        trcorner='╗',
        blcorner='╚',
        brcorner='╝'
    )

    # Create the main pile with spacing
    main_pile = urwid.Pile([
        # Messages window
        ('fixed', WindowSize.RX_HEIGHT, receive_box),
        # Space between receive and status
        ('fixed', 1, urwid.Filler(urwid.Divider())),
        # Status window with proper height
        ('fixed', WindowSize.ST_HEIGHT, status_box),
        # Space between status and transmit
        ('fixed', 1, urwid.Filler(urwid.Divider())),
        # Transmit window
        ('fixed', WindowSize.TX_HEIGHT, transmit_box)
    ])

    # Wrap pile in Columns for fixed width
    main_cols = urwid.Columns([
        ('fixed', WindowSize.MAX_COL, main_pile)
    ])

    # Create final frame
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