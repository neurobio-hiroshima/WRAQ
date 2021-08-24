# -*- coding: utf-8 -*-
"""
Script for convert WRAQ-Wifi output (.csv) file to ActogramJ (ImageJ plugin) compatible input data file.

author: Deepa Kasaragod
email: deepa@hiroshima-u.ac.jp
license: GPL-3.0 License
    
Please cite the following paper if you adopt this code for your research.   
Zhu et al., A novel microcontroller-based system for the wheel running activity in mice (2021). 

Please use or modify the file freely for your purpose, keeping the above information. 
    
"""

from WRAQ import WRAQ
import sys

if __name__ == '__main__':   
    args = sys.argv
    WR = WRAQ("wraq-wifi", period=24)
    if len(args) < 2:
        print("Enter the start time to correct ZT: Parameter not input")
        sys.exit()

    WR.wraq2actj('JST', str(args[1])) # Time zone is JST. 
    
 