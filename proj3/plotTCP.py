import optparse
import sys

import matplotlib
from pylab import *

# Parses a file of rates and plot a sequence number graph. Black
# squares indicate a sequence number being sent and dots indicate a
# sequence number being ACKed.
class Plotter:
    def __init__(self,file):
        """ Initialize plotter with a file name. """
        self.file = file
        self.min_time = None
        self.max_time = None

    def plot(self, packetX, packetY, ackX, ackY, lostX, lostY ):
        """ Create a sequence graph of the packets. """
        clf()
        figure(figsize=(15,5))
        x = []
        y = []
        ackX = []
        ackY = []
        
        scatter(x,y,marker='s',s=3)
        scatter(ackX,ackY,marker='s',s=0.2)
        xlabel('Time (seconds)')
        ylabel('Sequence Number Mod 1000')
        xlim([self.min_time,self.max_time])
        savefig('sequence.png')

def parse_options():
        # parse options
        parser = optparse.OptionParser(usage = "%prog [options]",
                                       version = "%prog 0.1")

        parser.add_option("-f","--file",type="string",dest="file",
                          default=None,
                          help="file")

        (options,args) = parser.parse_args()
        return (options,args)


if __name__ == '__main__':
    (options,args) = parse_options()
    if options.file == None:
        print "plot.py -f file"
        sys.exit()
    p = Plotter(options.file)
    p.parse()
    p.plot()
