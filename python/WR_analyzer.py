# -*- coding: utf-8 -*-
"""
Created on Mon Apr  5 13:00:43 2021

@author: Deepa
"""


import tkinter
from tkinter import filedialog
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import datetime
import time
import sys 


class WRAQ(object):
    def __init__(self, argi, period):
        """
        

        Parameters
        ----------
        period : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """

        self.direc, self.filepath = self.getdirectory()
        self.radius =  4 # in cm
        self.cycleperiod = period
        self.timeres = 4 # in sec
        if (str(argi) == 'fire'):
            self.timeres = 300 # in sec
        self.n_sample = int(self.cycleperiod * 60 * 60/ self.timeres)
        self.n_perday_sample = int(24 * 60 * 60/ self.timeres)
        
    def getdirectory(self):
        """
        

        Returns
        -------
        direc : TYPE
            DESCRIPTION.
        filepath : TYPE
            DESCRIPTION.

        """


        root = tkinter.Tk()
        root.withdraw()
        filepath = filedialog.askopenfilename()
        direc = os.path.dirname(filepath)
        os.chdir(direc)
        self.outdir = direc + str('/out') 
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
        return direc, filepath
        
    def read_csvtopandas(self, fin):
        """
        

        Parameters
        ----------
        fin : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """ 
 
        self.df = pd.read_csv(fin, header=None)

    def distance_day(self, rev):  
        """
        

        Parameters
        ----------
        rev : TYPE
            DESCRIPTION.

        Returns
        -------
        distance : TYPE
            DESCRIPTION.

        """
        distance = 3.14 * 2 * self.radius * rev
        return distance
    
    def calc_speed(self, data, deltat):
        """
        

        Parameters
        ----------
        data : TYPE
            DESCRIPTION.
        deltat : TYPE
            DESCRIPTION.

        Returns
        -------
        speed: TYPE
            DESCRIPTION.

        """
       
        ret = np.cumsum(data, dtype=float)
        ret[deltat:] = ret[deltat:] - ret[:-deltat]
        return ret[deltat - 1:] / (deltat * 4)
            
    def plot_actogram_modulo(self, startdatetime):
        """
        

        Parameters
        ----------
        startdatetime : TYPE
            DESCRIPTION.

        Returns
        -------
        actogram_data : TYPE
            DESCRIPTION.

        """

        #print(startdatetime)
        if (startdatetime == '0'):
            df1 = self.df
            #print(df1)
        else:
            #print (self.df.index[df['DateandTime'] == startdatetime].values)
            df1 = self.df.iloc[self.df.index[df['DateandTime'] == startdatetime].values[0]:]
            df1.reset_index(inplace = True)
        self.trans_df = df1
        self.runningdays = int(len(df1) / self.n_perday_sample)
        actogram_data = np.zeros((self.runningdays, self.n_sample))
        for i in range(self.runningdays):
            #print(i)
            startind = i * self.n_perday_sample
            endind = (i + 1) * self.n_sample
            splitind = self.n_sample
            if (i == (self.runningdays - 1)):
                endind = i * self.n_perday_sample + len(df1) % self.n_sample
                splitind = len(df1) % self.n_sample               
            #print(splitind, startind, endind)
            actogram_data[i, 0:splitind] = df1['rev'].iloc[startind : endind]
            
        plt.figure(2, figsize=(10,7))
        plt.title('Double-plotted actogram')
        for jj in range(self.runningdays):
            plt.subplot(self.runningdays, 1, jj+1)
            plt.plot(actogram_data[jj])
            plt.ylim([0, 15])
        return actogram_data
 
if __name__ == '__main__':   

    
    args = sys.argv
    WR = WRAQ(str(args[2]), period=24)
    if len(args) < 3:
        print("Enter the start time to correct ZT: Parameter not input")
        sys.exit()
    fin = WR.filepath
    print(fin)
    
    WR.read_csvtopandas(fin)
    df =  WR.df 
    
    if (str(args[2]) == 'fire'):
        df['Date'] = pd.to_datetime(df[0]).dt.date
        k = pd.to_datetime(pd.to_datetime(df['Date']).dt.date.unique().tolist())
        
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Time'] = pd.to_datetime(df[0]).dt.time
        df['DateandTime'] = [datetime.datetime.combine(a, b) for a, b in zip(df['Date'], df['Time'])]
        df.columns = ['DateandTime-a', 'rev', 'illum', 'Date', 'Time', 'DateandTime']
    
    if (str(args[2]) == 'ada'):
        if (len(df.columns) == 3):
            df.columns = ['DateandTime', 'rev', 'illum']
            
        else:
            df.columns = ['Date', 'Time', 'rev', 'illum']
            df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y%m%d')
            df['Time'] = pd.to_datetime(df['Time']).dt.time
            df['DateandTime'] = [datetime.datetime.combine(a, b) for a, b in zip(df['Date'], df['Time'])]
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    rev_listperday = WR.plot_actogram_modulo(str(args[1]))
    df = WR.trans_df

    distperday = np.zeros(WR.runningdays)   
    for i in range(WR.runningdays):
        distperday[i] = WR.distance_day(np.sum(rev_listperday[i]))
     
    timeper = 3600 # average over 1 hour
    if (str(args[2]) == 'fire'):
        timeper = 60 # average over 1 hour
    speed = np.zeros((WR.runningdays, WR.n_perday_sample - timeper + 1))
    for ii in range(WR.runningdays):
        speed[ii] = WR.calc_speed(rev_listperday[ii], timeper)
        
    plt.figure(3, figsize=(10,7))
    for jj in range(WR.runningdays):
        plt.subplot(WR.runningdays, 1, jj+1)
        plt.plot(speed[jj])
        plt.ylim([0, 5])
    
    revperday = np.sum(rev_listperday, axis=1)
    durationperday = np.sum(rev_listperday, axis=1)* WR.timeres/(60)
    # if (str(args[2]) == 'fire'):
    #     durationperday = np.sum(rev_listperday, axis=1)*5
    
    #avgspeedperday = distperday/durationperday
    avgspeedperday = np.mean(speed, axis=1) 
    
    plt.figure(4, figsize=(10,7))
    plt.subplot(2,2,1)
    plt.plot(distperday)
    plt.xlabel('Days')
    plt.ylabel('Distance')
    plt.xlim([0, 25])
    #plt.ylim([0, 1300000])
    
    plt.subplot(2,2,2)
    plt.plot(durationperday)
    plt.xlabel('Days')
    plt.ylabel('Duration of activity')
    plt.xlim([0, 25])
    #plt.ylim([0, 500])
    
    plt.subplot(2,2,3)
    plt.plot(avgspeedperday)
    plt.xlabel('Days')
    plt.ylabel('Average Speed')
    plt.xlim([0, 25])
    #plt.ylim([0, 4000])
    
    plt.subplot(2,2,4)
    plt.plot(revperday)
    plt.xlabel('Days')
    plt.ylabel('Revolutions')
    plt.xlim([0, 25])
    #plt.ylim([0, 6500])
    
    fw=WR.outdir + str('/') + str(time.strftime("%Y%m%d")) + str('_') +  os.path.basename(WR.filepath).replace('.csv', 'outfile.csv').replace('.CSV', 'outfile.csv')
    datafin = np.array([distperday, durationperday, avgspeedperday, revperday])
    dfg = pd.DataFrame(datafin.T)
    dfg.to_csv(fw, index=True, header= ['Distance', 'Duration', 'Avg.speed', 'Revolution'])
    
    # figpath = (WR.outdir + str('/') + str(time.strftime("%Y%m%d")) + str('_') +  os.path.basename(WR.filepath).replace('.csv', 'out.png').replace('.CSV', 'out.png'))
    # if (os.path.exists(figpath) ==True):
    #     os.remove(figpath)    
    # plt.savefig(figpath, dpi = 600)
    
 
               


