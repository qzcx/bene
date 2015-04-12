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
from pylab import *

class AppHandler(object):
    def __init__(self,filename):
        self.filename = filename
        self.directory = 'received'
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.f = open("%s/%s" % (self.directory,self.filename),'w')

    def receive_data(self,data, packet):
        Sim.trace('AppHandler',"application got %d bytes" % (len(data)))
        self.f.write(data)
        self.f.flush()

class Main(object):
    def __init__(self):
        self.directory = 'received'
        self.parse_options()
        self.test()
        #self.diff()

    def parse_options(self):
        parser = optparse.OptionParser(usage = "%prog [options]",
                                       version = "%prog 0.1")

        parser.add_option("-f","--filename",type="str",dest="filename",
                          default='internet-architecture.pdf',
                          help="filename to send")

        parser.add_option("-l","--loss",type="float",dest="loss",
                          default=0.0,
                          help="random loss rate")

        parser.add_option("-d", "--dynamic",
                  action="store_true", dest="dynamic", default=False,
                  help="turn on dynamic timer")

        (options,args) = parser.parse_args()
        self.filename = options.filename
        self.loss = options.loss
        self.dyn_timer = options.dynamic

    def diff(self):
        args = ['diff','-u',self.filename,self.directory+'/'+self.filename]
        result = subprocess.Popen(args,stdout = subprocess.PIPE).communicate()[0]
        print
        if not result:
            print "File transfer correct!"
        else:
            print "File transfer failed. Here is the diff:"
            print
            print result

    def plot(self, packetX, packetY, ackX, ackY, lostX, lostY, limit, filename ):
        """ Create a sequence graph of the packets. """
        def modSeq(y): return (y /1000) % 50 

        clf()
        figure(figsize=(15,5))
        
        scatter(packetX[:limit],map(modSeq,packetY[:limit]),marker='s',s=3)
        scatter(lostX,map(modSeq,lostY),marker='x',color='black')

        scatter(ackX[:limit],map(modSeq,ackY[:limit]),marker='s',s=0.2)
        xlabel('Time (seconds)')
        ylabel('Sequence Number / 1000 % 50')
        xlim([-0.05,0.6])
        ylim([-5,55])

        savefig('%s.png' % filename)

    def run(self,threshold=100000, lostPackets=[], reno=False):
        # parameters
        Sim.scheduler.reset()
        Sim.set_debug('AppHandler')
        Sim.set_debug('TCP')

        # setup network
        net = Network('../networks/one-hop.txt')
        net.loss(self.loss)

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
        c1 = TCP(t1,n1.get_address('n2'),1,n2.get_address('n1'),1,a,
                threshold=threshold,dyn_timer=self.dyn_timer, lossPackets=lostPackets, reno=reno)
        c2 = TCP(t2,n2.get_address('n1'),1,n1.get_address('n2'),1,a,
                threshold=threshold,dyn_timer=self.dyn_timer)

        # send a file
        with open(self.filename,'r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=0, event=data, handler=c1.send)

        # run the simulation
        Sim.scheduler.run()
        return c1 #return the TCP connection so data can be analyzed

    def test(self):
        
        c1 = self.run()
        self.plot(packetX= c1.sentTime, packetY = c1.sentSeq, ackX=c1.ackTime, ackY=c1.ackSeq, 
                  lostX=c1.lostTime, lostY=c1.lostSeq, filename= "slow_start_new", limit=200)
        c1 = self.run(threshold=16000)
        self.plot(packetX= c1.sentTime, packetY = c1.sentSeq, ackX=c1.ackTime, ackY=c1.ackSeq, 
                  lostX=c1.lostTime, lostY=c1.lostSeq, filename= "additive_increase_new", limit=200)
        
        c1 = self.run(lostPackets=[31000])
        #print "sentTime",c1.sentTime
        self.plot(packetX= c1.sentTime, packetY = c1.sentSeq, ackX=c1.ackTime, ackY=c1.ackSeq, 
                  lostX=c1.lostTime, lostY=c1.lostSeq, filename= "AIMD_new", limit=500)
        c1 = self.run(lostPackets=[31000,32000,33000])
        self.plot(packetX= c1.sentTime, packetY = c1.sentSeq, ackX=c1.ackTime, ackY=c1.ackSeq, 
                  lostX=c1.lostTime, lostY=c1.lostSeq, filename= "burst_loss_new", limit=500)
        c1 = self.run(lostPackets=[31000,32000,33000,34000,35000])
        self.plot(packetX= c1.sentTime, packetY = c1.sentSeq, ackX=c1.ackTime, ackY=c1.ackSeq, 
                  lostX=c1.lostTime, lostY=c1.lostSeq, filename= "burst_loss_5_new", limit=500)
        c1 = self.run(lostPackets=[31000,32000,33000,34000,35000,62000])
        self.plot(packetX= c1.sentTime, packetY = c1.sentSeq, ackX=c1.ackTime, ackY=c1.ackSeq, 
                  lostX=c1.lostTime, lostY=c1.lostSeq, filename= "burst_loss_5_plus_end_new", limit=500)
        #Reno Tests
        c1 = self.run(lostPackets=[31000], reno=True)
        #print "sentTime",c1.sentTime
        self.plot(packetX= c1.sentTime, packetY = c1.sentSeq, ackX=c1.ackTime, ackY=c1.ackSeq, 
                  lostX=c1.lostTime, lostY=c1.lostSeq, filename= "AIMD_reno_new", limit=500)
        c1 = self.run(lostPackets=[31000,32000,33000], reno=True)
        self.plot(packetX= c1.sentTime, packetY = c1.sentSeq, ackX=c1.ackTime, ackY=c1.ackSeq, 
                  lostX=c1.lostTime, lostY=c1.lostSeq, filename= "burst_loss_reno_new", limit=500)


if __name__ == '__main__':
    m = Main()
