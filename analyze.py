import numpy
import time
import pandas as pd
import argparse
import sys

def log( *input ):
    if(debugFlag):
        print( *input )

columns = ['DAQ Temp',
                  'TT1: Run Tank',
                  'TT2: Pre-Injectior Temp',
                  'TT3: Pre-CC Temp',
                  'TT4: Detached',
                  'PT1', # pressure transducer 1
                  'PT2',
                  'unknown8',
                  'unknown9',
                  'unknown10',
                  'unknown11',
                  'RunTank Mass', # mass of run tank
                  'Thrust',
                  'unknown14',
                  'time']

parser = argparse.ArgumentParser()

parser.add_argument('-i','-inputPath', nargs='?', const = 'hotfire.csv', help='raw data path', default = 'hotfire.csv', dest='rawPath')
parser.add_argument('-ref10', nargs='?', const = 49.07142857, type=float, help='Raw sensor data * [THIS ARGUMENT] = Pressure in Bar', default = 49.07142857, dest='psi1000calibration')
parser.add_argument('-ref16', nargs='?', const = 29.21428571, type=float, help='Raw sensor data * [THIS ARGUMENT] = Pressure in Bar', default = 29.21428571, dest='psi1600calibration')
parser.add_argument('-d','-debug', nargs='?', const=True, help="display console output", default=False, dest='debugFlag')


results = parser.parse_args()

psi1000calibration = results.psi1000calibration; #set vars from args
psi1600calibration = results.psi1600calibration;
rawPath = results.rawPath;
debugFlag = results.debugFlag;

log("\nCONSTANTS:\nCalibration value for 1000 psi transducer = ", psi1000calibration)
log("Calibration value for 1600 psi transducer = ", psi1600calibration)
log("Path of input file = ", rawPath)

log('\nBEGINNING DATA IMPORT')
raw = pd.read_csv(rawPath,names=columns)
log('DATA IMPORT COMPLETE')
log('\nRaw Imported Data File Sample:\n',raw.tail(8));

test = raw #create new variable for cleaned up data

test.time -= test.time[0]; #normalize time to first index
test.time = pd.to_timedelta(raw.time, unit="ms") #convert to time datatype
