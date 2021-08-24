# -*- coding: utf-8 -*-
"""
Script for analyzing WRAQ data to obtain per day activity output of voluntary mouse activity in home cage.

author: Deepa Kasaragod
email: deepa@hiroshima-u.ac.jp  , For bug reports, questions and feedback
license: GPL-3.0 License
    
Please cite the following paper if you adopt this code for your research.   
Zhu et al., A novel microcontroller-based system for the wheel running activity in mice (2021). 

Please use or modify the file freely for your purpose, keeping the above information. 
    
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