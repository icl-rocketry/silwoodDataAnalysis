import numpy
import time
import pandas as pd
import argparse
import sys

parser = argparse.ArgumentParser()

parser.add_argument('-i', nargs='?', const = 'hotfire.csv', help='raw data path', default = 'hotfire.csv', dest='rawPath')
parser.add_argument('-ref10', nargs='?', const = 49.07142857, type=float, help='Raw sensor data * [THIS ARGUMENT] = Pressure in Bar', default = 49.07142857, dest='psi1000calibration')
parser.add_argument('-ref16', nargs='?', const = 29.21428571, type=float, help='Raw sensor data * [THIS ARGUMENT] = Pressure in Bar', default = 29.21428571, dest='psi1600calibration')


results = parser.parse_args()

psi1000calibration = results.psi1000calibration; #set vars from args
psi1600calibration = results.psi1600calibration;
rawPath = results.rawPath;

print(psi1000calibration)
print(psi1600calibration)
print(rawPath)
