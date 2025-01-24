#!/usr/bin/env python3
import urwid
import asyncio

class LoRaUI:
    def __init__(self):
        # Receive window
        self.receive_listbox = urwid.ListBox(urwid.SimpleFocusListWalker([
            urwid.Text("Welcome to LoRa Interface")
        ]))
        
        # Status bar
        self.status_text = urwid.Text("Ready")
        
        # Transmit input
        self.transmit_edit = urwid.Edit("> ")
        
        # Layout
        self.main_pile = urwid.Pile([
            urwid.LineBox(self.receive_listbox),
            ('pack', self.status_text),
            ('pack', self.transmit_edit)
        ])

    def add_message(self, message):
        """Add message to receive window"""
        self.receive_listbox.body.append(urwid.Text(message))
        self.receive_listbox.set_focus(len(self.receive_listbox.body) - 1)

async def xcvr():
    ui = LoRaUI()
    
    def unhandled_input(key):
        if key == 'q':
            raise urwid.ExitMainLoop()
        if key == 'enter':
            # Simulate message sending
            ui.add_message(f"Sent: {ui.transmit_edit.edit_text}")
            ui.transmit_edit.set_edit_text("")
        return False
    
    # Create event loop
    event_loop = urwid.AsyncioEventLoop(loop=asyncio.get_event_loop())
    
    # Create main loop
    main_loop = urwid.MainLoop(
        ui.main_pile, 
        event_loop=event_loop,
        unhandled_input=unhandled_input
    )
    
    # Simulate periodic messages
    async def periodic_messages():
        for i in range(5):
            await asyncio.sleep(1)
            ui.add_message(f"Simulated message {i}")
    
    # Run periodic messages concurrently
    task = asyncio.create_task(periodic_messages())
    
    try:
        main_loop.run()
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

def main():
    asyncio.run(xcvr())

if __name__ == '__main__':
    main()
    