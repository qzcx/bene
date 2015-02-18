import sys
sys.path.append('..')

from src.sim import Sim
from src.node import Node
from src.link import Link
from src.transport import Transport
from src.tcp import TCP

from networks.network import Network

import optparse
import os
import subprocess

import matplotlib
matplotlib.use('Agg')
from pylab import *

class AppHandler(object):
    def __init__(self,filename):
        self.filename = filename
        self.directory = 'received'
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.f = open("%s/%s" % (self.directory,self.filename),'w')

    def receive_data(self,data,packet):
        #Sim.trace('AppHandler',"application got %d bytes" % (len(data)))
        self.f.write(data)
        self.f.flush()
        global count
        global tot_delay
        tot_delay += packet.queueing_delay
        count += 1

class Main(object):
    def __init__(self):
        self.throughput = []
        self.delay = []
        self.window_sizes = [1000,2000,5000,10000,15000,20000]
        self.directory = 'received'
        self.parse_options()
        self.get_data()
        self.graphData()
        #self.graph_timeout()

    def parse_options(self):
        parser = optparse.OptionParser(usage = "%prog [options]",
                                       version = "%prog 0.1")

        parser.add_option("-f","--filename",type="str",dest="filename",
                          default='internet-architecture.pdf',
                          help="filename to send")

        (options,args) = parser.parse_args()
        self.filename = options.filename

    def get_data(self):
        global count
        global tot_delay
        tot_delay = 0
        count = 0
        for window in self.window_sizes:
            size,timeout_hist = self.run(loss=0, window=window)
            print "size",size
            print "time", Sim.scheduler.current_time()
            self.throughput.append(float(size)/Sim.scheduler.current_time())
            if count != 0:
                self.delay.append(tot_delay/count)
            tot_delay = 0
            count = 0
        

    def graphData(self):
        clf()

        plot(self.window_sizes,self.throughput)
        xlabel('window_size')
        ylabel('throughput')
        savefig('throughput.png')
        
        clf()
        plot(self.window_sizes,self.delay)
        xlabel('window_size')
        ylabel('queueing_delay')
        savefig('queueing_delay.png')

    def graph_timeout(self):
        size,timeout_hist = self.run(loss=0.1, window=10000)
        clf()
        plot(timeout_hist)
        xlabel('packet #')
        ylabel('timeout')
        savefig('timeout.png')

    def run(self, loss, window):
        # parameters
        Sim.scheduler.reset()
        Sim.set_debug('AppHandler')
        Sim.set_debug('TCP')

        # setup network
        net = Network('../networks/one-hop.txt')
        net.loss(loss)

        # setup routes
        n1 = net.get_node('n1')
        n2 = net.get_node('n2')
        n1.add_forwarding_entry(address=n2.get_address('n1'),link=n1.links[0])
        n2.add_forwarding_entry(address=n1.get_address('n2'),link=n2.links[0])

        # setup transport
        t1 = Transport(n1)
        t2 = Transport(n2)

        # setup application
        a = AppHandler(self.filename)

        # setup connection
        c1 = TCP(t1,n1.get_address('n2'),1,n2.get_address('n1'),1,a,window=window,dyn_timer=True)
        c2 = TCP(t2,n2.get_address('n1'),1,n1.get_address('n2'),1,a,window=window,dyn_timer=True)

        size = 0
        # send a file
        with open(self.filename,'r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                size += len(data)
                Sim.scheduler.add(delay=0, event=data, handler=c1.send)

        # run the simulation
        Sim.scheduler.run()
        return size,c1.timeout_hist

if __name__ == '__main__':

    m = Main()