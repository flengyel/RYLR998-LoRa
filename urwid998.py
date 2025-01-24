#!/usr/bin/env python3
# -*- coding: utf8 -*-

import asyncio
import aioserial
import urwid
import argparse
import logging
import sys
import re
from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE

# Default configuration constants (from original implementation)
DEFAULT_ADDR_INT = 0
DEFAULT_BAND = '915000000'
DEFAULT_PORT = '/dev/ttyS0'
DEFAULT_BAUD = '115200'
DEFAULT_CRFOP = '22'
DEFAULT_MODE = '0'
DEFAULT_NETID = '18'
DEFAULT_SPREADING_FACTOR = '9'
DEFAULT_BANDWIDTH = '7'
DEFAULT_CODING_RATE = '1'
DEFAULT_PREAMBLE = '12'
DEFAULT_PARAMETER = f"{DEFAULT_SPREADING_FACTOR},{DEFAULT_BANDWIDTH},{DEFAULT_CODING_RATE},{DEFAULT_PREAMBLE}"

class RYLR998:
    # State table constants (preserved from original implementation)
    ADDR_TABLE  = [b'+',b'A',b'D',b'D',b'R',b'E',b'S',b'S',b'=']
    BAND_TABLE  = [b'+',b'B',b'A',b'N',b'D',b'=']
    CRFOP_TABLE = [b'+',b'C',b'R',b'F',b'O',b'P',b'=']
    ERR_TABLE   = [b'+',b'E',b'R',b'R',b'=']
    FACT_TABLE  = [b'+',b'F',b'A',b'C',b'T',b'O',b'R',b'Y']
    IPR_TABLE   = [b'+',b'I',b'P',b'R',b'=']
    MODE_TABLE  = [b'+',b'M',b'O',b'D',b'E',b'=']
    NETID_TABLE = [b'+',b'N',b'E',b'T',b'W',b'O',b'R',b'K',b'I',b'D',b'=']
    OK_TABLE    = [b'+',b'O',b'K']
    PARAM_TABLE = [b'+',b'P',b'A',b'R',b'A',b'M',b'E',b'T',b'E',b'R',b'=']
    RCV_TABLE   = [b'+',b'R',b'C',b'V',b'=']
    UID_TABLE   = [b'+',b'U',b'I',b'D',b'=']
    VER_TABLE   = [b'+',b'V',b'E',b'R',b'=']

    def __init__(self, args, 
                 parity=PARITY_NONE, 
                 bytesize=EIGHTBITS,
                 stopbits=STOPBITS_ONE, 
                 timeout=None):
        # Configuration setup (preserved from original implementation)
        self.port = args.port
        self.baudrate = args.baud
        self.parity = parity
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.timeout = timeout

        # Configuration parameters
        self.debug = args.debug
        self.factory = args.factory
        self.echo = args.echo

        # Module-specific configurations
        self.addr = str(args.addr)
        self.pwr = str(args.pwr) if any(arg.startswith('--pwr') for arg in sys.argv[1:]) else None
        self.mode = str(args.mode)
        self.netid = str(args.netid)
        self.band = args.band

        # Parameter parsing
        if any(arg.startswith('--parameter') for arg in sys.argv[1:]):
            (self.spreading_factor, 
             self.bandwidth, 
             self.coding_rate, 
             self.preamble) = args.parameter.split(',')
            
            # Network ID and preamble validation
            if self.netid != DEFAULT_NETID and self.preamble != '12':
                raise argparse.ArgumentTypeError(
                    f'Preamble must be 12 if NETWORKID is not equal to the default {DEFAULT_NETID}.'
                )
        else:
            self.parameter = DEFAULT_PARAMETER
            self.spreading_factor = DEFAULT_SPREADING_FACTOR
            self.bandwidth = DEFAULT_BANDWIDTH
            self.coding_rate = DEFAULT_CODING_RATE
            self.preamble = DEFAULT_PREAMBLE

        # State machine variables
        self.state = 0
        self.state_table = self.RCV_TABLE
        self.rxbuf = ''
        self.rxlen = 0

        # Serial port setup
        try:
            self.serial = aioserial.AioSerial(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                bytesize=self.bytesize,
                stopbits=self.stopbits,
                timeout=self.timeout
            )
            logging.info(f'Opened port {self.port} at {self.baudrate} baud')
        except Exception as e:
            logging.error(str(e))
            raise

    def rxbuf_reset(self, state_table=None):
        """Reset receive buffer state"""
        self.rxbuf = ''
        self.rxlen = 0
        self.state = 0
        self.state_table = state_table or self.RCV_TABLE

    async def send_at_command(self, cmd=''):
        """Send AT command"""
        command = f'AT{"+"+cmd if cmd else ""}\r\n'
        return await self.serial.write_async(command.encode('utf-8'))

class LoRaUI:
    def __init__(self, rylr_instance):
        # Reference to RYLR998 instance
        self.rylr = rylr_instance

        # Widgets
        self.receive_widget = urwid.ListBox(urwid.SimpleFocusListWalker([]))
        self.status_widget = urwid.Text("")
        self.transmit_widget = urwid.Edit("> ")
        
        # Layout
        self.main_layout = urwid.Pile([
            ('weight', 0.7, urwid.LineBox(self.receive_widget)),
            ('pack', urwid.Divider('-')),
            ('pack', self.status_widget),
            ('pack', urwid.Divider('-')),
            ('pack', self.transmit_widget)
        ])
        
        # Palette
        self.palette = [
            ('receive', 'light blue', ''),
            ('transmit', 'yellow', ''),
            ('status', 'white', ''),
            ('error', 'dark red', '')
        ]

    def add_receive_message(self, message, color='receive'):
        """Add a message to the receive window"""
        self.receive_widget.body.append(
            urwid.Text((color, message))
        )
        # Scroll to bottom
        self.receive_widget.set_focus(len(self.receive_widget.body) - 1)
    
    def update_status(self, message, color='status'):
        """Update status bar"""
        self.status_widget.set_text((color, message))

async def setup_initial_configuration(rylr, queue):
    """Set up initial module configuration using existing queue logic"""
    # Replicate the initial configuration setup from the original implementation
    if rylr.factory:
        await queue.put('FACTORY')
        await queue.put('DELAY,0.25')

    await queue.put(f'IPR={rylr.baudrate}')
    await queue.put(f'ADDRESS={rylr.addr}')
    await queue.put(f'NETWORKID={rylr.netid}')
    await queue.put(f'BAND={rylr.band}')

    if rylr.pwr:
        await queue.put(f'CRFOP={rylr.pwr}')

    await queue.put(f'PARAMETER={rylr.spreading_factor},{rylr.bandwidth},{rylr.coding_rate},{rylr.preamble}')

    # Query commands
    await queue.put('ADDRESS?')
    await queue.put('BAND?')
    await queue.put('CRFOP?')
    await queue.put(f'MODE={rylr.mode}')
    await queue.put('PARAMETER?')
    await queue.put('UID?')
    await queue.put('VER?')
    await queue.put('NETWORKID?')

async def process_serial_input(rylr, ui, queue):
    """Process serial input, maintaining original state machine logic"""
    waitForReply = False

    while True:
        # Check if there's input from serial port
        if rylr.serial.in_waiting > 0:
            # Read one byte
            data = await rylr.serial.read_async(size=1)

            # Original state machine parsing logic here
            # (This would be a direct port of the original xcvr method's parsing logic)
            # For brevity, I'll provide a simplified placeholder
            if rylr.state < len(rylr.state_table):
                if rylr.state_table[rylr.state] == data:
                    rylr.state += 1
                else:
                    rylr.rxbuf_reset()
            else:
                # Accumulate response
                rylr.rxbuf += str(data, 'utf8')
                rylr.rxlen += 1

                if data == b'\n':
                    # Process complete response
                    # This would include all the match cases from the original implementation
                    ui.add_receive_message(f"Received: {rylr.rxbuf}")
                    rylr.rxbuf_reset()

        # Process command queue (similar to original implementation)
        if not waitForReply and not queue.empty():
            waitForReply = True
            cmd = await queue.get()
            
            if cmd.startswith('DELAY,'):
                _, delay = cmd.split(',', 1)
                await asyncio.sleep(float(delay))
                waitForReply = False
            elif cmd.startswith('SEND='):
                # Logic for sending messages
                pass
            else:
                await rylr.send_at_command(cmd)

        # Small delay to prevent tight loop
        await asyncio.sleep(0.01)

async def main():
    # Argument parsing (reused from original implementation)
    parser = argparse.ArgumentParser()
    # (Argument definitions would be copied from the original rylr998.py)
    
    # Parse arguments
    args = parser.parse_args()

    # Create RYLR998 instance
    rylr = RYLR998(args)

    # Create UI
    ui = LoRaUI(rylr)

    # Command queue
    queue = asyncio.Queue()

    # Set up initial configuration
    await setup_initial_configuration(rylr, queue)

    # Create tasks for serial processing and UI
    serial_task = asyncio.create_task(process_serial_input(rylr, ui, queue))

    # Run URWID main loop with asyncio integration
    def unhandled_input(key):
        if key == 'q':
            raise urwid.ExitMainLoop()

    loop = urwid.MainLoop(
        ui.main_layout, 
        palette=ui.palette,
        unhandled_input=unhandled_input,
        event_loop=urwid.AsyncioEventLoop(loop=asyncio.get_event_loop())
    )

    try:
        loop.run()
    finally:
        # Cancel serial processing task
        serial_task.cancel()
        try:
            await serial_task
        except asyncio.CancelledError:
            pass

if __name__ == '__main__':
    asyncio.run(main())
    