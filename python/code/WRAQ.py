# -*- coding: utf-8 -*-
"""
Script for analyzing WRAQ data for voluntary mouse activity in home cage

Details redacted for BLIND REVIEW

"""

import tkinter
from tkinter import filedialog
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import datetime
import time 


class WRAQ(object):
    """
    A class for analyzing WRAQ data for volunatry mouse activity in home cage

    ...

    Attributes
    ----------
    wraqtype : str
        type of wraq system used for the data acquisition
    direc : str
        Folder of the data file
    filepath : str
        Filepath of the data file
    radius : str
        radius of the wheel used  in cm
    cycleperiod : int
        the moduloperiod for actogram calculation
    timeres : str
        time resolution of the data acquisition in seconds
    n_sample : str
        total number of data sample points saved
    n_perday_sample : int
        number of data sample points per day


    Methods
    -------
    get_filepath()
        Opens the dialog box to select the .csv file of the wheelrunner activity.
             
    read_csvtopandas()
        Read the csv file as pandas dataframe
    
    wraq2actj(timezone, startdatetime)
        Convert the WRAQ data to actogramj compatible file with time stamp in UTC or JST
    
    distance_day(rev)
        Calculate distance travelled per day.
    
    actogram_modulo(startdatetime)
        get actogram data over cycleperiod
        
    perday_activity(startdatetime)
        output the .csv file as per day average activity which includes 
           'Presumptive distance travelled/day (cm)'
           'Total duration of activity/day (minutes)'
           'Number of Revolutions/day' 
           
           Per day refers to 24 hour period starting from zetigeber time12
           as set by the startdatetime
    
    """   
    def __init__(self, wraqtype, period):
        """
        

        Parameters
        ----------
        wraqtype : TYPE
            wraq or wraq-wifi
        period : TYPE
            24 for 24 hour modulo actogram 

        Returns
        -------
        None.

        """

        self.wraqtype = wraqtype
        self.direc, self.filepath = self.get_filepath()
        self.radius =  4 # in cm
        self.cycleperiod = period
        self.timeres = 4 # in sec
        if (str(wraqtype) == 'wraq-wifi'):
            self.timeres = 300 # in sec
        self.n_sample = int(self.cycleperiod * 60 * 60/ self.timeres)
        self.n_perday_sample = int(24 * 60 * 60/ self.timeres)
        
    def get_filepath(self):
        """
        

        Returns
        -------
        direc : TYPE
            full path of directory of the data file (.csv) to be analyzed
        filepath : TYPE
            full filepath of .csv file

        """

        root = tkinter.Tk()
        root.withdraw()
        filepath = filedialog.askopenfilename()
        direc = os.path.dirname(filepath)
        os.chdir(direc)
        self.outdir = direc + str('/out') 
        return direc, filepath
        
    def read_csvtopandas(self):
        """
        

        Returns
        -------
        None.

        """
        self.df = pd.read_csv(self.filepath, header=None)
        
        
    def wraq2actj(self, timezone, startdatetime):
        """
        

        Parameters
        ----------
        timezone : TYPE
            'UTC' or 'JST'
            
        startdatetime : TYPE
            time starts at zeitgeber time 12 . input the ZT12
            format of startdatetime is  YYYY-MM-DD HH:MM:SS" example "2021-08-20 23:05:01" 
            if no correction needed startdatetime  = "0"

        Returns
        -------
        .csv file compatible with ActogramJ

        """

        fin = self.filepath
        #print(fin)
        fbase = os.path.splitext(fin)[0]
        fext = os.path.splitext(fin)[1]
        fout = fbase + '_padded' + fext
        if (self.wraqtype == 'wraq'):
            self.read_csvtopandas()
            df = self.df
            if (len(df.columns) == 3):
                df.columns = ['DateandTime', 'rev', 'illum']
                
            else:
                df.columns = ['Date', 'Time', 'rev', 'illum']
                df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y%m%d')
                df['Time'] = pd.to_datetime(df['Time']).dt.time
                df['DateandTime'] = [datetime.datetime.combine(a, b) for a, b in zip(df['Date'], df['Time'])]
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            if (startdatetime == '0'):
                df1 = df.copy()
            else:
                df1 = df.copy()
                df1 = df.iloc[df.index[df['DateandTime'] == startdatetime].values[0]:]
                df1.reset_index(inplace = False)
            df1.to_csv(fout, index=False, header=False)  
                    
        if (self.wraqtype == 'wraq-wifi'):
            df = pd.read_csv(fin) # to keep the header
            #print(df)
            df.created=pd.to_datetime(df.created)
            df.columns = ['created', 'd1', 'd2', 'd3',
                          'd4', 'd5', 'd6', 'd7', 'd8']
            df = df.sort_values('created')
            df = df.set_index('created')
            if (timezone == 'UTC'):
                df.index = pd.to_datetime(df.index) + pd.DateOffset(hours=9)
                ts_onset = pd.Timestamp(df.index[0].date()).tz_localize('UTC')
                ts_onset = ts_onset - pd.DateOffset(1) + pd.DateOffset(hours=9)
            if (timezone == 'JST'):
                df.index = pd.to_datetime(df.index).tz_localize(None)
                ts_onset = pd.Timestamp(df.index[0].to_pydatetime()).tz_localize(None)
                
            df1 = df.copy()
            df1.reset_index(inplace = True)
            if (startdatetime != '0'):
                df1 = df1.iloc[df1.index[df1['created'] == startdatetime].values[0]:]
                df1.reset_index(inplace = False)
                              
            row_df = pd.DataFrame({'d1':[0], 'd2':[0]}, index=[ts_onset])
            df = pd.concat([row_df, df])
            newd1 = df.resample('5T')['d1'].sum()
            newd2 = df.resample('5T')['d2'].sum()
            df = pd.concat([newd1, newd2], axis=1)
            df1.to_csv(fout, index=False, header=False)  
 
        print(fin + ': successfully converted into ' + fout)

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
            
    def actogram_modulo(self, startdatetime):
        """
        

        Parameters
        ----------
        startdatetime : TYPE
            time starts at zeitgeber time 12 . input the ZT12
            format of startdatetime is  YYYY-MM-DD HH:MM:SS" example "2021-08-20 23:05:01" 
            if no correction needed startdatetime  = "0"

        Returns
        -------
        actogram_data : TYPE
            DESCRIPTION.

        """

        #print(startdatetime)
        if (startdatetime == '0'):
            df1 = self.df
        else:
            df = self.df
            df1 = df.iloc[df.index[df['DateandTime'] == startdatetime].values[0]:]
            df1.reset_index(inplace = True)
        self.trans_df = df1
        self.runningdays = int(len(df1) / self.n_perday_sample)
        actogram_data = np.zeros((self.runningdays, self.n_sample))
        for i in range(self.runningdays):
            startind = i * self.n_perday_sample
            endind = (i + 1) * self.n_sample
            splitind = self.n_sample
            if (i == (self.runningdays - 1)):
                endind = i * self.n_perday_sample + len(df1) % self.n_sample
                splitind = len(df1) % self.n_sample               
            actogram_data[i, 0:splitind] = df1['rev'].iloc[startind : endind]
            
        return actogram_data
    
    def perday_activity(self, startdatetime):
        """
        

        Parameters
        ----------
        startdatetime : TYPE
            time starts at zeitgeber time 12 . input the ZT12
            format of startdatetime is  YYYY-MM-DD HH:MM:SS" example "2021-08-20 23:05:01" 
            if no correction needed startdatetime  = "0"
            

        Returns
        -------
        Saves .csv file under 'out' folder within the data directory with the average activity per day
        (zeitgeber time used for day calculations)

        """
        fin = self.filepath
        self.read_csvtopandas()
        df =  self.df 
        
        if (self.wraqtype == 'wraq-wifi'):
            df['Date'] = pd.to_datetime(df[0]).dt.date          
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Time'] = pd.to_datetime(df[0]).dt.time
            df['DateandTime'] = [datetime.datetime.combine(a, b) for a, b in zip(df['Date'], df['Time'])]
            df.columns = ['DateandTime-a', 'rev', 'illum', 'Date', 'Time', 'DateandTime']
        
        if (self.wraqtype  == 'wraq'):
            if (len(df.columns) == 3):
                df.columns = ['DateandTime', 'rev', 'illum']
                
            else:
                df.columns = ['Date', 'Time', 'rev', 'illum']
                df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y%m%d')
                df['Time'] = pd.to_datetime(df['Time']).dt.time
                df['DateandTime'] = [datetime.datetime.combine(a, b) for a, b in zip(df['Date'], df['Time'])]
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        rev_listperday = self.actogram_modulo(startdatetime)
        df = self.trans_df
    
        distperday = np.zeros(self.runningdays)   
        for i in range(self.runningdays):
            distperday[i] = self.distance_day(np.sum(rev_listperday[i]))

        revperday = np.sum(rev_listperday, axis=1)
        durationperday = np.sum(rev_listperday, axis=1)* self.timeres/(60) 
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
        fw=self.outdir + str('/') + str(time.strftime("%Y%m%d")) + str('_') +  os.path.basename(self.filepath).replace('.csv', 'outfile.csv').replace('.CSV', 'outfile.csv')
        datafin = np.array([distperday, durationperday, revperday])
        dfg = pd.DataFrame(datafin.T)
        dfg.index += 1 # start index at 1
        dfg.to_csv(fw, index=True, index_label='Day_id', header= ['Presumptive distance travelled/day (cm)', 'Total duration of activity/day (minutes)', 'Number of Revolutions/day'])
 
if __name__ == '__main__':   

    print("")
