import sys
sys.path.append('..')

from src.sim import Sim
from src import node
from src import link
from src import packet

from networks.network import Network

import random as random1

import optparse

import matplotlib
matplotlib.use('Agg')
from pylab import *

class Generator(object):
    def __init__(self,node,destination,load,duration):
        self.node = node
        self.load = load
        self.duration = duration
        self.start = 0
        self.ident = 1
        self.destination = destination

    def handle(self,event):
        # quit if done
        now = Sim.scheduler.current_time()
        if (now - self.start) > self.duration:
            return

        # generate a packet
        self.ident += 1
        p = packet.Packet(destination_address=self.destination,ident=self.ident,protocol='delay',length=1000)
        Sim.scheduler.add(delay=0, event=p, handler=self.node.send_packet)
        # schedule the next time we should generate a packet
        Sim.scheduler.add(delay=random1.expovariate(self.load), event='generate', handler=self.handle)




class DelayHandler(object):
    def receive_packet(self,packet):
        global count
        global tot_delay
        tot_delay += packet.queueing_delay
        count += 1

def calc_avg_delay(loadFactor):
    # parameters
    Sim.scheduler.reset()

    # setup network
    net = Network('../networks/one-hop.txt')

    # setup routes
    n1 = net.get_node('n1')
    n2 = net.get_node('n2')
    n1.add_forwarding_entry(address=n2.get_address('n1'),link=n1.links[0])
    n2.add_forwarding_entry(address=n1.get_address('n2'),link=n2.links[0])

    # setup app
    d = DelayHandler()
    net.nodes['n2'].add_protocol(protocol="delay",handler=d)

    # setup packet generator
    destination = n2.get_address('n1')
    max_rate = 1000000/(1000*8)
    load = loadFactor*max_rate
    g = Generator(node=n1,destination=destination,load=load,duration=10)
    Sim.scheduler.add(delay=0, event='generate', handler=g.handle)
    
    # run the simulation
    Sim.scheduler.run()
    print "average =", tot_delay/count,"count =",count

    return tot_delay/count

def plot_results(trials,results):
    """ Create a line graph of an equation. """
    clf()

    plot(trials,results)

    
    x = np.arange(0,1,0.01)
    u = 1000000.0/(1000.0*8.0)
    plot(x,(1/(2*u))*x/(1-x),label='Theory',color="green")

    xlabel('utilization')
    ylabel('1/(2u) x p/(1-p)')
    savefig('equation.png')


if __name__ == '__main__':
    trials = [.10,.20,.30,.40,.50,.60,.70,.80,.90,.95,.97,.98,]
    results = []
    global count
    global tot_delay
    tot_delay = 0
    count = 0
    for load in trials:
        results.append(calc_avg_delay(load))
        count = 0
        tot_delay = 0
    plot_results(trials,results)
        

    
