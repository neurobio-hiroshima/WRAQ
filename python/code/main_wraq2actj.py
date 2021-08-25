# -*- coding: utf-8 -*-
"""
Script for convert WRAQ-Wifi output (.csv) file to ActogramJ (ImageJ plugin) compatible input data file.

Details redacted for BLIND REVIEW

"""

from WRAQ import WRAQ
import sys

if __name__ == '__main__':   
    args = sys.argv
    WR = WRAQ(str(args[1]), period=24)
    if len(args) < 3:
        print("Enter the start time to correct ZT: Parameter not input")
        sys.exit()
    WR.wraq2actj('JST', str(args[2])) # Time zone is JST. 