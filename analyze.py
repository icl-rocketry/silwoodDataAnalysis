import time
import pandas as pd
import argparse
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy import integrate

def log( *input ):
    if(debugFlag):
        print( *input ) #if the debug flag is set print whatever is passed to log

def finish( *filename ):
    if(isEmbeddedFlag):
        plt.savefig(filename[0]) #if the script is running in embedded mode save the plot
    #else:
        #plt.show(block=True) #if it isnt, print the plot

smoothingFactor = 10 #how much the burn detection algorithm should smooth the data (increase this if the data is noisy and the program can't identify the burn)
margin = 20 #how many data rows the burn detection algorithm will pad the calculated burn start and end points with (increase if the burn gets cut off)
burnDetectionSensitivity = 0.9 #0 - 1, higher = more sensitive, 0.5 is a good starting val (decrease if the algorithm is detecting a random spike as part of the burn)

columns = ['DAQ Temp',
                  'TT1: Run Tank',
                  'TT2: Pre-Injectior Temp',
                  'TT3: Pre-CC Temp',
                  'TT4: Detached',
                  'PT1', # pressure transducer 1
                  'PT2',
                  'PT3',
                  'PT4',
                  'PT5',
                  #'unknown8',
                  #'unknown9',
                  #'unknown10',
                  'unknown11',
                  'RunTank Mass', # mass of run tank
                  'Thrust',
                  'unknown14',
                  'time']

parser = argparse.ArgumentParser()

parser.add_argument('-i','-inputPath', nargs='?', const = 'hotfire.csv', help='raw data path', default = 'hotfire.csv', dest='rawPath')
parser.add_argument('-ref10', nargs='?', const = 49.07142857, type=float, help='(Raw sensor data - offset) / [THIS ARGUMENT] = Pressure in Bar', default = 49.07142857, dest='psi1000calibration')
parser.add_argument('-ref16', nargs='?', const = 29.21428571, type=float, help='(Raw sensor data - offset) / [THIS ARGUMENT] = Pressure in Bar', default = 29.21428571, dest='psi1600calibration')
parser.add_argument('-off16', nargs='?', const = None, type=float, help='(Raw sensor data - [THIS ARGUMENT] / calibration factor = Pressure in Bar', default = None, dest='psi1600offset')
parser.add_argument('-ff','-forceCalibrationFactor', nargs='?', const = 90436, type=float, help='(Raw sensor data - offset) / [THIS ARGUMENT] = Pressure in Bar', default = 90436, dest='forceCalibration')
parser.add_argument('-fo','-forceCalibrationOffset', nargs='?', const = None, type=float, help='(Raw sensor data - [THIS ARGUMENT] / calibration factor = Pressure in Bar', default = None, dest='forceOffset')
parser.add_argument('-d','-debug', nargs='?', const=True, help="display console output", default=False, dest='debugFlag')
parser.add_argument('-e','-plotToFile', nargs='?', const=True, help="output plots to png file instead of displaying them", default=False, dest='isEmbeddedFlag')
parser.add_argument('-bStart', nargs='?', const = None, type=int, help='manually specify index where burn starts', default = None, dest='burnStart')
parser.add_argument('-bEnd', nargs='?', const = None, type=int, help='manually specify index where burn ends', default = None, dest='burnEnd')
parser.add_argument('-start', nargs='?', const = None, type=int, help='manually cut off data before index', default = None, dest='rangeStart')
parser.add_argument('-end', nargs='?', const = None, type=int, help='manually cut off data after index', default = None, dest='rangeEnd')


results = parser.parse_args()

psi1000calibration = results.psi1000calibration; #set vars from args
psi1600calibration = results.psi1600calibration;
psi1600offset = results.psi1600offset;
rawPath = results.rawPath;
debugFlag = results.debugFlag;
isEmbeddedFlag = results.isEmbeddedFlag;
burnStart = results.burnStart;
burnEnd = results.burnEnd;
rangeEnd = results.rangeEnd;
rangeStart = results.rangeStart;
forceCalibration = results.forceCalibration;
forceOffset = results.forceOffset;

log("\nCONSTANTS:\nCalibration value for 1000 psi transducer = ", psi1000calibration)
log("Calibration value for 1600 psi transducer = ", psi1600calibration)
log("Path of input file = ", rawPath)

log('\nBEGINNING DATA IMPORT')

raw = pd.read_csv(rawPath,names=columns)
raw = raw.loc[rangeStart:rangeEnd].reset_index()

log('DATA IMPORT COMPLETE')
log('\nRaw Imported Data File Sample:\n',raw.head(8));

log('\nBEGIN CLEANING UP DATA')
test = raw #create new variable for cleaned up data

raw.time -= raw.time[0]; #normalize time to first index
test.timeRaw = raw.time
test.time = pd.to_timedelta(raw.time, unit="ms") #convert to time datatype

test.PT1 /= psi1600calibration; #divide pressure values by calibration data
test.PT2 /= psi1000calibration;
test.PT3 /= psi1600calibration;
test.PT4 /= psi1600calibration;
test.PT5 /= psi1000calibration;
test.Thrust *= -1 #makes thrust data positive if it's negative

#AUTOMATIC PRESSURE GAUGE OFFSET CALCULATION
if psi1600offset is None:
    psi1600offset = test.PT2.tail(1000).median(); #PT5 is open to the air and should be at 0 after the test. Take the median of the last 1000 datapoints and use it as the offset
else:
    psi1600offset /= psi1600calibration #Otherwise use the provided calibration factor

#AUTOMATIC THRUST OFFSET CALCULATION
if forceOffset is None:
    forceOffset = test.Thrust.head(100).median(); #PT5 is open to the air and should be at 0 after the test. Take the median of the last 1000 datapoints and use it as the offset
else:
    psi1600offset /= psi1600calibration #Otherwise use the provided calibration factor

log('Calculated pressure gauge offset = ', psi1600offset*psi1600calibration)

log()

test.PT1 -= psi1600offset;
test.PT2 -= psi1600offset;
test.PT3 -= psi1600offset;
test.PT4 -= psi1600offset;
test.PT5 -= psi1600offset*psi1600calibration/psi1000calibration;
mama = test.time

test.Thrust -= forceOffset
test.Thrust /= forceCalibration

joe = test.Thrust
chungus = test.timeRaw

log('\nData Cleanup Finished - Sample:\n',test.tail(8))

#FIND BURNS
meanData = test.filter(items=["PT1", "PT2", "PT3", "PT4", "PT5"]).prod(axis=1) ** 1.0/5 #take the geometric avg of all pressure columns
smoothedMean = meanData.ewm(span=smoothingFactor).mean(); #smooth out data so algorithm can identify major peaks (burns)
maxMean = smoothedMean.max() #find max value (assumed to be occuring during the burn)

maxMeanIndex = smoothedMean.idxmax() #find index of max value
maxPT5 = test.Thrust.iloc[maxMeanIndex-1000:maxMeanIndex+1000].max() #find the max pt5 value in the area surrounding that index
maxMeanIndex = test.Thrust.iloc[maxMeanIndex-1000:maxMeanIndex+1000].idxmax() #find the index of that max value

log('Max Thrust = ',maxPT5)
log(maxMeanIndex)
log(test.Thrust[maxMeanIndex])


dataAfterMax = joe.iloc[maxMeanIndex:] #create a temp array consting of all the data points after the max PT1 time index
dataBeforeMax = joe.iloc[:maxMeanIndex].iloc[::-1] #create a temp array consting of all the data points before the max PT1 time index

log('dataBeforeMax',dataBeforeMax.head(20))

dataAfterMax[dataAfterMax < maxPT5*(1-burnDetectionSensitivity)] = None; #set all the values in each index below a certain threshold to N
dataBeforeMax[dataBeforeMax < maxPT5*(1-burnDetectionSensitivity)] = None;

log('dataBeforeMax',dataBeforeMax.head(20))

log(dataBeforeMax.last_valid_index())
log(dataAfterMax.last_valid_index())

if burnStart is None: burnStart = dataBeforeMax.last_valid_index() - margin; # find the first index which isn't 'None' and add a margin
if burnEnd is None: burnEnd = dataAfterMax.last_valid_index() + margin; # find the last index which isn't 'None' and add a margin

log('\nBurn Start: ',test.time[burnStart])
log('Burn End: ',test.time[burnEnd])
log('Burn Duration: ', test.timeRaw[burnEnd] - test.timeRaw[burnStart] - 2*margin, 'ms')
65
test = test.iloc[burnStart:burnEnd] #get rid of all non-burn data

log("\nFinal Data Sample:",test.head(16))

chungus /= 1000 #convert ms to s
impulse = integrate.trapezoid(test.Thrust,chungus.iloc[burnStart:burnEnd])*1000

#CREATE PLOTS
ax = test.plot(x="time", y=["PT1", "PT2", "PT3", "PT4", "PT5"])
finish("pressure.png")

ax = test.plot(x="time", y=["Thrust"])
finish("thrust.png")

log('\nHOTFIRE STATS\nMax Thrust: ', maxPT5, 'Kn')
log('Maximum Chamber Pressure: ', test.PT2.max(), 'Bar')
log('Average Chamber Pressure: ', test.PT2.mean(), 'Bar')

log('Estimated Impulse: ', impulse, 'Ns')




if not isEmbeddedFlag: plt.show();
