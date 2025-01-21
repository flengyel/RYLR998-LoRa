#!/usr/bin/env python3
# -*- coding: utf8 -*-

import logging
import argparse
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
    