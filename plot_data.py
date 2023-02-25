import time
import os
import plotext as plt
import sys
from sh import tail

def get_name(x):
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
                      'unknown15']
    return columns[x]

def follow(thefile):
    '''generator function that yields new lines in a file
    '''
    # seek the end of the file
    thefile.seek(0, os.SEEK_END)
    
    # start infinite loop
    while True:
        # read last line of file
        line = thefile.readline().rstrip('\n')
        # sleep if file hasn't been updated
        if not line:
            time.sleep(0.1)
            continue

        yield line

if __name__ == '__main__':
    nvar = int(sys.argv[1])
    # initialise plot
    try:
        plt.title(sys.argv[2])
    except:
        plt.title(f"Streaming data {sys.argv[1]}")
    #plt.title(get_name(nvar))
        
    filepath = "/home/pi/data-out.csv"

    queue = [0.0 for i in range(50)] # initialise queue
    maxval = 0.0
    minval = 0.0
    plt.clc()
    # iterate over the generator
    # Line will be a csv string
    # Read in values, apply transformations to real units
    # add to queue, then plot
    
    i = 0
    for line in tail("-f", filepath, _iter=True):
        i = i+1
        if i%8 == 0: # Update with every 8th value
            i = 0
            try:
                x = float(line.strip("\n").split(',')[nvar])
                # Add new data to queue
                queue.append(x)
                if queue[0] == maxval:
                    maxval = queue[1]
                elif queue[0] == minval:
                    minval = queue[1]

                queue.pop(0)
                # Plot new data. TODO: Subplots
                plt.clt() # clear terminal
                plt.cld() # clear data
                plt.plot(queue) # plot new data
                plt.show() # show plot

                if x > maxval:
                    maxval = x
                    plt.ylim(0.9*minval, 1.1*maxval)
                elif x < minval:
                    minval = x
                    plt.ylim(0.9*minval, 1.1*maxval)
                    
            except KeyboardInterrupt:
                break
            except:
                pass

