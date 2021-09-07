# -*- coding: utf-8 -*-
"""
Script for analyzing WRAQ data to obtain per day activity output of voluntary mouse activity in home cage.

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
    WR.perday_activity(str(args[2]))