#!/usr/bin/env python3
# -*- coding: utf8 -*-

import logging
import argparse
import re
from src.ui.constants import RadioLimits

def bandcheck(n: str) -> str:
    """
    Validate frequency band input.
    Args:
        n: String containing frequency in Hz
    Returns:
        Original string if valid
    Raises:
        ArgumentTypeError if frequency outside valid range
    """
    try:
        f = int(n)
        if f < RadioLimits.MIN_FREQ or f > RadioLimits.MAX_FREQ:
            error_msg = f"Frequency must be in range ({RadioLimits.MIN_FREQ}..{RadioLimits.MAX_FREQ})"
            logging.error(error_msg)
            raise argparse.ArgumentTypeError(error_msg)
        return n
    except ValueError:
        error_msg = f"Frequency must be a number"
        logging.error(error_msg)
        raise argparse.ArgumentTypeError(error_msg)

def pwrcheck(n: str) -> str:
    """
    Validate power output setting.
    Args:
        n: String containing power in dBm
    Returns:
        Original string if valid
    Raises:
        ArgumentTypeError if power outside valid range
    """
    try:
        p = int(n)
        if p < RadioLimits.MIN_POWER or p > RadioLimits.MAX_POWER:
            error_msg = f"Power output must be in range ({RadioLimits.MIN_POWER}-{RadioLimits.MAX_POWER})"
            logging.error(error_msg)
            raise argparse.ArgumentTypeError(error_msg)
        return n
    except ValueError:
        error_msg = f"Power must be a number"
        logging.error(error_msg)
        raise argparse.ArgumentTypeError(error_msg)

# Pattern compilation at module level
MODE_PATTERN = re.compile('^(0)|(1)|(2,(\\d{2,5}),(\\d{2,5}))$')
NETID_PATTERN = re.compile(f'^{"|".join(str(x) for x in range(RadioLimits.MIN_NETID, RadioLimits.MAX_NETID + 1))}|{RadioLimits.ALT_NETID}')
UART_PATTERN = re.compile('^(/dev/tty(S|USB)|COM)\\d{1,3}')


def modecheck(s: str) -> str:
    """
    Validate mode setting.
    Args:
        s: String containing mode (0, 1, or 2,delay1,delay2)
    Returns:
        Original string if valid
    Raises:
        ArgumentTypeError if mode format invalid or delays out of range
    """
    p = MODE_PATTERN.match(s)
    if p is not None:
        if p.group(1) is not None or p.group(2) is not None:
            return s
        # mode 2
        r_ms = int(p.group(4))
        s_ms = int(p.group(5))
        if (RadioLimits.MIN_MODE_DELAY < r_ms < RadioLimits.MAX_MODE_DELAY) and \
           (RadioLimits.MIN_MODE_DELAY < s_ms < RadioLimits.MAX_MODE_DELAY):
            return s
    error_msg = "Mode must match 0|1|2,30..60000,30..60000"
    logging.error(error_msg)
    raise argparse.ArgumentTypeError(error_msg)

def netidcheck(s: str) -> str:
    """
    Validate network ID.
    Args:
        s: String containing network ID
    Returns:
        Original string if valid
    Raises:
        ArgumentTypeError if ID not in valid range
    """
    if NETID_PATTERN.match(s):
        return str(s)
    error_msg = f'NETWORK ID must match {RadioLimits.MIN_NETID}..{RadioLimits.MAX_NETID}|{RadioLimits.ALT_NETID}'
    logging.error(error_msg)
    raise argparse.ArgumentTypeError(error_msg)

def uartcheck(s: str) -> str:
    """
    Validate serial port device name.
    Args:
        s: String containing device path
    Returns:
        Original string if valid
    Raises:
        ArgumentTypeError if path format invalid
    """
    if UART_PATTERN.match(s):
        return s
    
    error_msg = "Serial Port device name not of the form ^(/dev/tty(S|USB)|COM)\\d{1,3}$"
    
    logging.error(error_msg)
    
    raise argparse.ArgumentTypeError(error_msg)
