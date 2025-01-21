#!/usr/bin/env python3
# -*- coding: utf8 -*-

import logging
from typing import Optional
import aioserial
from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE

class SerialManager:
    """Manages non-blocking serial communication"""
    
    def __init__(self, port: str, baudrate: str):
        """Initialize and open serial port"""
        self.port = port
        self.baudrate = baudrate
        self._serial: Optional[aioserial.AioSerial] = None
        self._open()  # Open port during initialization

    def _open(self) -> None:
        """Open serial port with fixed 8N1 parameters"""
        try:
            self._serial = aioserial.AioSerial(
                port=self.port,
                baudrate=self.baudrate,
                parity=PARITY_NONE,
                bytesize=EIGHTBITS,
                stopbits=STOPBITS_ONE,
                timeout=None
            )
            logging.info(f'Opened port {self.port} at {self.baudrate} baud')
        except Exception as e:
            logging.error(f"Failed to open serial port: {str(e)}")
            raise

    def close(self) -> None:
        """Close serial port if open"""
        if self._serial:
            try:
                self._serial.close()
            except Exception as e:
                logging.error(f"Error closing serial port: {str(e)}")

    def has_data(self) -> bool:
        """Check if data is available without blocking"""
        if not self._serial:
            return False
        return self._serial.in_waiting > 0

    async def read_byte(self) -> bytes:
        """
        Read a single byte if available.
        Should only be called after checking has_data()
        """
        if not self._serial:
            raise RuntimeError("Serial port not opened")
        return await self._serial.read_async(size=1)

    async def write(self, data: bytes) -> int:
        """Write data to serial port"""
        if not self._serial:
            raise RuntimeError("Serial port not opened")
        return await self._serial.write_async(data)
    
    