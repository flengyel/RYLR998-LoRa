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
        error_msg = "Frequency must be a number"
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
        error_msg = "Power must be a number"
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

# Pattern for parameter validation
PARAM_PATTERN = re.compile('^([7-9]|1[01]),([7-9]),([1-4]),([4-9]|1\\d|2[0-5])$')

def check_sf_bw_compatibility(sf: str, bw: str) -> bool:
    """
    Check if spreading factor and bandwidth values are compatible.
    Returns True if compatible, False otherwise.
    """
    _sf = int(sf)
    _bw = int(bw)
    return (_bw == 7 and _sf < 10) or \
           (_bw == 8 and _sf < 11) or \
           (_bw == 9 and _sf < 12)

def paramcheck(s: str) -> str:
    """
    Validate LoRa parameters string.
    Args:
        s: String containing SF,BW,CR,Preamble values
    Returns:
        Original string if valid
    Raises:
        ArgumentTypeError if parameters invalid or incompatible
    """
    if not PARAM_PATTERN.match(s):
        error_msg = 'PARAMETER: argument must match 7..11,7..9,1..4,4..24'
        logging.error(error_msg + ' subject to constraints on spreading factor, bandwidth and NETWORK ID')
        raise argparse.ArgumentTypeError(error_msg + ' subject to constraints on spreading factor, bandwidth and NETWORK ID')
    
    # Check SF/BW compatibility
    sf, bw, _, _ = s.split(',')
    if not check_sf_bw_compatibility(sf, bw):
        error_msg = 'PARAMETER: Incompatible spreading factor and bandwidth values'
        logging.error(error_msg)
        raise argparse.ArgumentTypeError(error_msg)
    
    return s

def validate_netid_parameter(netid: str, parameter: str) -> None:
    """
    Validate parameter preamble when netid is not default.
    Args:
        netid: Network ID string
        parameter: Full parameter string
    Raises:
        ArgumentTypeError if preamble invalid for non-default netid
    """
    from src.ui.constants import RadioDefaults

    if netid != RadioDefaults.NETID:
        _, _, _, preamble = parameter.split(',')
        if preamble != str(RadioLimits.DEFAULT_PREAMBLE):
            error_msg = f'Preamble must be {RadioLimits.DEFAULT_PREAMBLE} if NETWORKID is not equal to the default {RadioDefaults.NETID}'
            logging.error(error_msg)
            raise argparse.ArgumentTypeError(error_msg)
