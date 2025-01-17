        add_label(self.VFO_ROW, self.VFO_COL, self.VFO_LABEL, self.VFO_LEN)
        add_label(self.PWR_ROW, self.PWR_COL, self.PWR_LABEL, self.PWR_LEN)
        add_label(self.NETID_ROW, self.NETID_COL, self.NETID_LABEL, self.NETID_LEN)
        self.window.noutrefresh()

    def update_field(self, label: str, value: str, color_pair: int):
        """Update a status field value"""
        if label == 'lora':
            self.window.addnstr(self.TXRX_ROW, self.TXRX_COL, 
                              self.TXRX_LABEL, self.TXRX_LEN, 
                              cur.color_pair(color_pair))
        elif label == 'addr':
            self.window.addstr(0, 13, value, cur.color_pair(color_pair))
        elif label == 'rssi':
            self.window.addstr(0, 26, value, cur.color_pair(color_pair))
        elif label == 'snr':
            self.window.addstr(0, 36, value, cur.color_pair(color_pair))
        elif label == 'vfo':
            self.window.addstr(self.VFO_ROW, self.VFO_COL + 4, 
                             value, cur.color_pair(color_pair))
        elif label == 'pwr':
            self.window.addstr(self.PWR_ROW, self.PWR_COL + 4, 
                             value, cur.color_pair(color_pair))
        elif label == 'netid':
            self.window.addstr(self.NETID_ROW, 37, value, cur.color_pair(color_pair))
        self.window.noutrefresh()

class ReceiveWindow:
    """Message receive window handling"""
    def __init__(self, parent_win, pos: WindowPosition):
        self.window = parent_win.derwin(pos.height, pos.width, pos.row, pos.col)
        self.window.scrollok(True)
        self.window.bkgd(' ', cur.color_pair(ColorScheme.YELLOW_BLACK))
        self.row = 0
        self.col = 0
        self.max_row = pos.height - 1

    def _scroll_if_needed(self):
        """Scroll window if at bottom"""
        if self.row == self.max_row:
            self.window.scroll()

    def _advance_row(self):
        """Move to next row, handling scrolling"""
        self.row = min(self.max_row, self.row + 1)
        self.col = 0

    def add_message(self, msg: str, length: int, color_pair: int):
        """Add message with scrolling"""
        self._scroll_if_needed()
        self.window.addnstr(self.row, self.col, msg, length, cur.color_pair(color_pair))
        self._advance_row()
        self.window.noutrefresh()

    def insert_message(self, msg: str, length: int, color_pair: int):
        """Insert message without scrolling if at max length"""
        self._scroll_if_needed()
        self.window.insnstr(self.row, self.col, msg, length, cur.color_pair(color_pair))
        self._advance_row()
        self.window.noutrefresh()

class TransmitWindow:
    """Message transmission window handling"""
    def __init__(self, parent_win, pos: WindowPosition):
        self.window = parent_win.derwin(pos.height, pos.width, pos.row, pos.col)
        self.window.nodelay(True)
        self.window.keypad(True)
        self.window.notimeout(False)
        self.window.bkgd(' ', cur.color_pair(ColorScheme.YELLOW_BLACK))
        self.row = 0
        self.col = 0

    def get_input(self) -> int:
        """Get input character"""
        return self.window.getch()

    def move_cursor(self, row: int, col: int):
        """Move cursor to specified position"""
        self.row = row
        self.col = col
        self.window.move(self.row, self.col)
        self.window.noutrefresh()

    def clear_line(self):
        """Clear current line"""
        self.window.erase()
        self.window.noutrefresh()

    def write_line(self, text: str, length: int):
        """Write text to current line"""
        if length <= 40:  # Maximum line length
            self.window.addnstr(self.row, 0, text, length)
            self.window.noutrefresh()

class Display:
    """Main display manager"""
    MAX_ROW = 28
    MAX_COL = 42

    def __init__(self, screen):
        locale.setlocale(locale.LC_ALL, '')
        cur.savetty()
        cur.raw()
        screen.nodelay(True)
        screen.bkgd(' ', cur.color_pair(ColorScheme.WHITE_BLACK))

        self.colors = ColorScheme()
        self.border_win = screen.derwin(self.MAX_ROW, self.MAX_COL, 0, 0)
        self._draw_borders()

        # Create sub-windows
        self.receive = ReceiveWindow(self.border_win, 
                                   WindowPosition(1, 1, 20, 40))
        self.status = StatusWindow(self.border_win,
                                 WindowPosition(22, 1, 3, 40))
        self.transmit = TransmitWindow(self.border_win,
                                     WindowPosition(26, 1, 1, 40))

    def _draw_borders(self):
        """Draw window borders and divisions"""
        self.border_win.border()
        
        # Draw horizontal divisions
        for y in [21, 23, 25]:
            self.border_win.addch(y, 0, cur.ACS_LTEE)
            self.border_win.hline(y, 1, cur.ACS_HLINE, self.MAX_COL-2)
            self.border_win.addch(y, self.MAX_COL-1, cur.ACS_RTEE)

        # Draw vertical divisions for status area
        for y, x in [(21, 7), (21, 20), (21, 31)]:
            self.border_win.addch(y, x, cur.ACS_TTEE)
            self.border_win.vline(y+1, x, cur.ACS_VLINE, 1)
            self.border_win.addch(y+2, x, cur.ACS_BTEE)

        # Draw vertical divisions for transmit area
        for x in [16, 25]:
            self.border_win.addch(23, x, cur.ACS_TTEE)
            self.border_win.addch(24, x, cur.ACS_VLINE)
            self.border_win.addch(25, x, cur.ACS_BTEE)

        self.border_win.noutrefresh()

    def update(self):
        """Update display"""
        cur.doupdate()

    def cleanup(self):
        """Restore terminal state"""
        cur.noraw()
        cur.resetty()
