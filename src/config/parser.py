#!/usr/bin/env python3
# -*- coding: utf8 -*-

import argparse
from src.ui.constants import RadioLimits, RadioDefaults, SerialDefaults

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser()

    # General options
    parser.add_argument('--debug', action='store_true',
                       help='log DEBUG information')
    parser.add_argument('--factory', action='store_true',
                       help='Factory reset to manufacturer defaults')
    parser.add_argument('--noGPIO', action='store_true',
                       help="Do not use rPI.GPIO module even if available")

    # RYLR998 configuration
    rylr998_config = parser.add_argument_group('rylr998 config')
    
    rylr998_config.add_argument('--addr', 
        required=False,
        type=int,
        choices=range(RadioLimits.MIN_ADDR, RadioLimits.MAX_ADDR + 1),
        metavar=f'[{RadioLimits.MIN_ADDR}..{RadioLimits.MAX_ADDR}]',
        dest='addr',
        default=RadioDefaults.ADDR,
        help=f'Module address ({RadioLimits.MIN_ADDR}..{RadioLimits.MAX_ADDR}). Default is {RadioDefaults.ADDR}')

    rylr998_config.add_argument('--band',
        required=False,
        type=str,
        metavar=f'[{RadioLimits.MIN_FREQ}..{RadioLimits.MAX_FREQ}]',
        dest='band',
        default=RadioDefaults.FREQ,
        help=f'Module frequency in Hz. Default: {RadioDefaults.FREQ}')

    rylr998_config.add_argument('--pwr',
        required=False,
        type=str,
        metavar=f'[{RadioLimits.MIN_POWER}..{RadioLimits.MAX_POWER}]',
        dest='pwr',
        default=RadioDefaults.POWER,
        help=f'RF power output in dBm. Default: {RadioDefaults.POWER}')

    rylr998_config.add_argument('--mode',
        required=False,
        type=str,
        metavar=f'[0|1|2,{RadioLimits.MIN_MODE_DELAY}..{RadioLimits.MAX_MODE_DELAY},'
                f'{RadioLimits.MIN_MODE_DELAY}..{RadioLimits.MAX_MODE_DELAY}]',
        dest='mode',
        default=RadioDefaults.MODE,
        help='Mode 0: transceiver, 1: sleep, 2,x,y: cycle')

    rylr998_config.add_argument('--netid',
        required=False,
        type=str,
        metavar=f'[{RadioLimits.MIN_NETID}..{RadioLimits.MAX_NETID}|{RadioLimits.ALT_NETID}]',
        dest='netid',
        default=RadioDefaults.NETID,
        help=f'NETWORK ID. Default: {RadioDefaults.NETID}')

    # parameter help text broken into multiple lines for readability
    param_help = (
        'LoRa parameters (SF,BW,CR,Preamble). '
        f'SF={RadioLimits.MIN_SF}..{RadioLimits.MAX_SF}, '
        f'BW={RadioLimits.MIN_BW}..{RadioLimits.MAX_BW} '
        f'(7=125kHz, 8=250kHz, 9=500kHz), '
        f'CR={RadioLimits.MIN_CR}..{RadioLimits.MAX_CR}, '
        f'Preamble={RadioLimits.MIN_PREAMBLE}..{RadioLimits.MAX_PREAMBLE} '
        f'(must be {RadioLimits.DEFAULT_PREAMBLE} if NETID≠18)'
    )
    
    default_param = (f"{RadioDefaults.SF},{RadioDefaults.BW},"
                    f"{RadioDefaults.CR},{RadioDefaults.PREAMBLE}")
    
    rylr998_config.add_argument('--parameter',
        required=False,
        type=str,
        metavar=f'[{RadioLimits.MIN_SF}..{RadioLimits.MAX_SF},'
                f'{RadioLimits.MIN_BW}..{RadioLimits.MAX_BW},'
                f'{RadioLimits.MIN_CR}..{RadioLimits.MAX_CR},'
                f'{RadioLimits.MIN_PREAMBLE}..{RadioLimits.MAX_PREAMBLE}]',
        dest='parameter',
        default=default_param,
        help=param_help)

    rylr998_config.add_argument('--echo',
        action='store_true',
        help='Retransmit received message')

    # Serial port configuration
    serial_config = parser.add_argument_group('serial port config')
    
    serial_config.add_argument('--port',
        required=False,
        type=str,
        metavar='[/dev/ttyS0../dev/ttyS999|/dev/ttyUSB0../dev/ttyUSB999|COM0..COM999]',
        default=SerialDefaults.PORT,
        dest='port',
        help=f'Serial port device name. Default: {SerialDefaults.PORT}')

    baudchoices = '(' + '|'.join(SerialDefaults.VALID_BAUDRATES) + ')'
    
    serial_config.add_argument('--baud',
        required=False,
        type=str,
        metavar=baudchoices,
        default=SerialDefaults.BAUD,
        dest='baud',
        choices=SerialDefaults.VALID_BAUDRATES,
        help=f'Serial port baudrate. Default: {SerialDefaults.BAUD}')

    return parser

def parse_args():
    """Parse command line arguments"""
    parser = create_parser()
    return parser.parse_args()
