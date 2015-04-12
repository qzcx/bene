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

_1MBPS = 1000000

class Main(object):
    def __init__(self):
        self.color = ["black","blue","yellow","green","orange"]
        self.directory = 'received'
        self.parse_options()
        self.run_tests()
        #self.diff()

    def parse_options(self):
        parser = optparse.OptionParser(usage = "%prog [options]",
                                       version = "%prog 0.1")

        parser.add_option("-l","--loss",type="float",dest="loss",
                          default=0.0,
                          help="random loss rate")

        parser.add_option("-d", "--dynamic",
                  action="store_true", dest="dynamic", default=False,
                  help="turn on dynamic timer")

        (options,args) = parser.parse_args()
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

    def run(self,threshold=100000, lostPackets=[], reno=False, queue_size=None, 
        additive_decrease=False, use_fix=True):
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

        #set queue size
        n1.links[0].queue_size = queue_size

        # setup transport
        t1 = Transport(n1)
        t2 = Transport(n2)

        # setup application
        a = AppHandler(self.filename)
        
        # setup connection
        c1 = TCP(t1,n1.get_address('n2'),1,n2.get_address('n1'),1,a,
            additive_decrease=additive_decrease,use_fix=use_fix)
        c2 = TCP(t2,n2.get_address('n1'),1,n1.get_address('n2'),1,a,
            additive_decrease=additive_decrease,use_fix=use_fix)

        # send a file
        with open(self.filename,'r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=0, event=data, handler=c1.send)

        # run the simulation
        Sim.scheduler.run()
        return c1,c2,n1 #return both TCP connections so data can be analyzed


    def run_two(self,threshold=100000, lostPackets=[], reno=False, queue_size=None, 
        c1_mult_const = 0.5, c3_mult_const = 0.5):
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

        #set queue size
        n1.links[0].queue_size = queue_size

        # setup transport
        t1 = Transport(n1)
        t2 = Transport(n2)

        # setup application
        a = AppHandler(self.filename)
        
        # setup connection
        c1 = TCP(t1,n1.get_address('n2'),1,n2.get_address('n1'),1,a, mult_const=c1_mult_const)
        c2 = TCP(t2,n2.get_address('n1'),1,n1.get_address('n2'),1,a)
        
        a2 = AppHandler(self.filename)

        # setup connection
        c3 = TCP(t1,n1.get_address('n2'),2,n2.get_address('n1'),2,a2, mult_const=c3_mult_const)
        c4 = TCP(t2,n2.get_address('n1'),2,n1.get_address('n2'),2,a2)

        # send a file
        with open(self.filename,'r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=0, event=data, handler=c1.send)
                Sim.scheduler.add(delay=0, event=data, handler=c3.send)

        # run the simulation
        Sim.scheduler.run()
        return c1,c2,c3,c4,n1 #return both TCP connections so data can be analyzed

    def run_five(self,threshold=100000, lostPackets=[], reno=False, queue_size=None,use_fix=True):
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

        #set queue size
        n1.links[0].queue_size = queue_size

        # setup transport
        t1 = Transport(n1)
        t2 = Transport(n2)

        # setup application
        a = AppHandler(self.filename)
        
        c = []
        # setup connection
        c.append(TCP(t1,n1.get_address('n2'),1,n2.get_address('n1'),1,a,use_fix=use_fix))
        c.append(TCP(t2,n2.get_address('n1'),1,n1.get_address('n2'),1,a,use_fix=use_fix))
        
        a2 = AppHandler(self.filename)

        # setup connection
        c.append(TCP(t1,n1.get_address('n2'),2,n2.get_address('n1'),2,a2,use_fix=use_fix))
        c.append(TCP(t2,n2.get_address('n1'),2,n1.get_address('n2'),2,a2,use_fix=use_fix))

        a3 = AppHandler(self.filename)

        # setup connection
        c.append(TCP(t1,n1.get_address('n2'),3,n2.get_address('n1'),3,a3,use_fix=use_fix))
        c.append(TCP(t2,n2.get_address('n1'),3,n1.get_address('n2'),3,a3,use_fix=use_fix))

        a4 = AppHandler(self.filename)

        # setup connection
        c.append(TCP(t1,n1.get_address('n2'),4,n2.get_address('n1'),4,a4,use_fix=use_fix))
        c.append(TCP(t2,n2.get_address('n1'),4,n1.get_address('n2'),4,a4,use_fix=use_fix))

        a5 = AppHandler(self.filename)

        # setup connection
        c.append(TCP(t1,n1.get_address('n2'),5,n2.get_address('n1'),5,a5,use_fix=use_fix))
        c.append(TCP(t2,n2.get_address('n1'),5,n1.get_address('n2'),5,a5,use_fix=use_fix))

        # send a file
        with open(self.filename,'r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=0, event=data, handler=c[0].send)
                Sim.scheduler.add(delay=0.1, event=data, handler=c[2].send)
                Sim.scheduler.add(delay=0.2, event=data, handler=c[4].send)
                Sim.scheduler.add(delay=0.3, event=data, handler=c[6].send)
                Sim.scheduler.add(delay=0.4, event=data, handler=c[8].send)

        # run the simulation
        Sim.scheduler.run()
        return c,n1 #return both TCP connections so data can be analyzed

    def run_two_paths(self,use_fix=True):
        # parameters
        Sim.scheduler.reset()

        # setup network
        net = Network('two_path.txt')

        # setup routes
        n1 = net.get_node('n1')
        n2 = net.get_node('n2')
        n3 = net.get_node('n3')
        n4 = net.get_node('n4')

        #n1.add_forwarding_entry(address=n2.get_address('n1'),link=n1.links[0])
        n1.add_forwarding_entry(address=n3.get_address('n2'),link=n1.links[0])

        #n4.add_forwarding_entry(address=n2.get_address('n4'),link=n4.links[0])
        n4.add_forwarding_entry(address=n3.get_address('n2'),link=n4.links[0])

        n2.add_forwarding_entry(address=n1.get_address('n2'),link=n2.links[0])
        n2.add_forwarding_entry(address=n4.get_address('n2'),link=n2.links[1])
        n2.add_forwarding_entry(address=n3.get_address('n2'),link=n2.links[2])

        n3.add_forwarding_entry(address=n1.get_address('n2'),link=n3.links[0])
        n3.add_forwarding_entry(address=n4.get_address('n2'),link=n3.links[0])
        #n3.add_forwarding_entry(address=n2.get_address('n3'),link=n3.links[0])

        print "n1:",n1.forwarding_table
        print "n2" ,n2.forwarding_table
        print "n3:",n3.forwarding_table
        

        n1.links[0].bandwidth = _1MBPS
        n4.links[0].bandwidth = _1MBPS
        n2.links[0].bandwidth = _1MBPS
        n2.links[1].bandwidth = _1MBPS
        n2.links[2].bandwidth = _1MBPS
        n3.links[0].bandwidth = _1MBPS


        n1.links[0].propagation = 0.010 #10 ms
        n4.links[0].propagation = 0.100 #100 ms
        n2.links[0].propagation = 0.010 #10 ms
        n2.links[1].propagation = 0.100 #100 ms
        n2.links[2].propagation = 0.010 #10 ms
        n3.links[0].propagation = 0.010 #10 ms

        queue_size = 100
        #set queue size
        n1.links[0].queue_size = queue_size
        n2.links[2].queue_size = queue_size
        n4.links[0].queue_size = queue_size

        # setup transport
        t1 = Transport(n1)
        t2 = Transport(n2)
        t3 = Transport(n3)
        t4 = Transport(n4)

        # setup application
        a = AppHandler(self.filename)
        a2 = AppHandler(self.filename)

        # setup connection
        #from n1
        c1 = TCP(t1,n1.get_address('n2'),1,n3.get_address('n2'),1,a,use_fix=use_fix)
        c2 = TCP(t3,n3.get_address('n2'),1,n1.get_address('n2'),1,a,use_fix=use_fix)
        #from n4
        c3 = TCP(t4,n4.get_address('n2'),2,n3.get_address('n2'),2,a2,use_fix=use_fix)
        c4 = TCP(t3,n3.get_address('n2'),2,n4.get_address('n2'),2,a2,use_fix=use_fix)

        # send a file
        with open(self.filename,'r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=0, event=data, handler=c1.send)
                Sim.scheduler.add(delay=0, event=data, handler=c3.send)

        # run the simulation
        Sim.scheduler.run()
        return c1,c2,c3,c4,n1,n2

    def run_test(self,threshold=100000, lostPackets=[], reno=False, queue_size=None, additive_decrease=False):
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

        n1.links[0].bandwidth = _1MBPS * 1.5
        n2.links[0].bandwidth = _1MBPS * 1.5

        #set queue size
        n1.links[0].queue_size = queue_size

        # setup transport
        t1 = Transport(n1)
        t2 = Transport(n2)

        # setup application
        a = AppHandler(self.filename)
        
        # setup connection
        c1 = TCP(t1,n1.get_address('n2'),1,n2.get_address('n1'),1,a,
            additive_decrease=additive_decrease)
        c2 = TCP(t2,n2.get_address('n1'),1,n1.get_address('n2'),1,a,
            additive_decrease=additive_decrease)

        # send a file
        with open(self.filename,'r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=0, event=data, handler=c1.send)

        # run the simulation
        Sim.scheduler.run()
        return c1,c2,n1 #return both TCP connections so data can be analyzed

    def run_two_test(self,threshold=100000, lostPackets=[], reno=False, queue_size=None, 
        c1_mult_const = 0.5, c3_mult_const = 0.5, use_fix=True):
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

        n1.links[0].bandwidth = _1MBPS * 1.5
        n2.links[0].bandwidth = _1MBPS * 1.5

        #set queue size
        n1.links[0].queue_size = queue_size
        n2.links[0].queue_size = queue_size

        # setup transport
        t1 = Transport(n1)
        t2 = Transport(n2)

        # setup application
        a = AppHandler(self.filename)
        
        # setup connection
        c1 = TCP(t1,n1.get_address('n2'),1,n2.get_address('n1'),1,a, mult_const=c1_mult_const, use_fix=use_fix)
        c2 = TCP(t2,n2.get_address('n1'),1,n1.get_address('n2'),1,a, use_fix=use_fix)
        
        a2 = AppHandler(self.filename)

        # setup connection
        c3 = TCP(t1,n1.get_address('n2'),2,n2.get_address('n1'),2,a2, mult_const=c3_mult_const,use_fix=use_fix)
        c4 = TCP(t2,n2.get_address('n1'),2,n1.get_address('n2'),2,a2, use_fix=use_fix)

        # send a file
        with open(self.filename,'r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=0, event=data, handler=c1.send)
                Sim.scheduler.add(delay=5, event=data, handler=c3.send)

        # run the simulation
        Sim.scheduler.run()
        return c1,c2,c3,c4,n1 #return both TCP connections so data can be analyzed


    def plot_lab3(self, packetX, packetY, ackX, ackY, lostX, lostY, limit, filename):
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

    def plot_rate_time(self, recvTimeList, recvSizeList, filename):
        clf()
        figure(figsize=(15,5))
        color = ["black","blue","yellow","green","orange"]
        for i in range(0,len(recvTimeList)):
            recvTime = recvTimeList[i]
            recvSize = recvSizeList[i]
            avgTime,avgSize = self.calc_avg_size(recvTime,recvSize)
            if not avgSize:
                print "AvgSize is None. Problem with recvTime/recvSize"
                print "recvTime",recvTime
                print "recvSize",recvSize
                return

            plot(avgTime,avgSize,color=self.color[i])
        xlabel('Time (seconds)')
        ylabel('bits recieved per second')
        plt.gca().set_xlim(left=0)
        savefig('%s.png' % filename)

    def plot_window_time(self, windTimeList, windSizeList, filename):
        clf()
        figure(figsize=(15,5))
        for i in range(0,len(windTimeList)):
            plot(windTimeList[i],windSizeList[i],color=self.color[i])
        xlabel('Time (seconds)')
        ylabel('window size (bytes)')
        plt.gca().set_xlim(left=0)
        savefig('%s.png' % filename)

    def plot_queue_time(self, queueTime, queueSize, dropTime, dropSize, filename):
        clf()
        figure(figsize=(15,5))
        scatter(queueTime,queueSize,marker='s',s=3)
        scatter(dropTime,dropSize,marker='x',color='black')
        xlabel('Time (seconds)')
        ylabel('Queue Size (# of packets)')
        plt.gca().set_xlim(left=0)
        savefig('%s.png' % filename)

    def calc_avg_size(self,recvTime,recvSize):
        if len(recvTime) <= 0 or len(recvTime) != len(recvSize):
            return None,None
        avgTime = [0]
        avgSize = [0]
        minIndex = 0
        maxIndex = 0
        #window size of 1 second
        windowSize = 0.2
        #rolling average calculated every 1/10 of a second
        step = 0.05
        t = 0.1
        endPoint = recvTime[len(recvTime) - 1]
        #this while loop is used because python doesn't support normal for loops and range only works on integers
        while(t < endPoint): 
            #find the new bounds
            while maxIndex < len(recvTime) and recvTime[maxIndex] < t:
                maxIndex +=1
            while minIndex < len(recvTime) and recvTime[minIndex] < t - windowSize:
                minIndex += 1
            #sum the given range
            sizeSum = 0.0
            for i in range(minIndex, maxIndex + 1):
                sizeSum += recvSize[i]
            avgSize.append(sizeSum/min(t,windowSize))
            avgTime.append(t)
            t += step
        return avgTime,avgSize

    def run_tests(self):
        basic_tests = True
        advanced_tests = False
        zappala_tests = False
        self.filename = "1mb.txt"
        
        if zappala_tests:
            self.filename = "2mb.txt"
            c1,c2,n1 = self.run_test(queue_size=100,threshold=100000)
            self.plot_rate_time([c2.recvTime],[c2.recvSize], "basic_plot_rate_one")
            self.plot_window_time([c1.windTime],[c1.windSize], "basic_window_time_one")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "basic_queue_time_one")
        
            #with fix
            c1,c2,c3,c4,n1 = self.run_two_test(queue_size=100,threshold=100000)
            self.plot_rate_time([c2.recvTime,c4.recvTime],[c2.recvSize,c4.recvSize], "test_plot_rate")
            self.plot_window_time([c1.windTime,c3.windTime],[c1.windSize,c3.windSize], "test_window_time")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "test_queue_time")

            #without fix
            c1,c2,c3,c4,n1 = self.run_two_test(queue_size=100,threshold=100000,use_fix=False)
            self.plot_rate_time([c2.recvTime,c4.recvTime],[c2.recvSize,c4.recvSize], "test_no_fix_plot_rate")
            self.plot_window_time([c1.windTime,c3.windTime],[c1.windSize,c3.windSize], "test_no_fix_window_time")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "test_no_fix_queue_time")


        self.filename = "1mb.txt"   
        if basic_tests:  
            #run one flow
            c1,c2,n1 = self.run(queue_size=50)
            self.plot_rate_time([c2.recvTime],[c2.recvSize], "plot_rate_one")
            self.plot_window_time([c1.windTime],[c1.windSize], "window_time_one")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "queue_time_one")
        
            #run one flow, no fix
            c1,c2,n1 = self.run(queue_size=50, use_fix=False)
            self.plot_rate_time([c2.recvTime],[c2.recvSize], "plot_rate_one_no_fix")
            self.plot_window_time([c1.windTime],[c1.windSize], "window_time_one_no_fix")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "queue_time_one_no_fix")

            #run two flows
            c1,c2,c3,c4,n1 = self.run_two(queue_size=100)
            self.plot_rate_time([c2.recvTime,c4.recvTime],[c2.recvSize,c4.recvSize], "plot_rate_two")
            self.plot_window_time([c1.windTime,c3.windTime],[c1.windSize,c3.windSize], "window_time_two")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "queue_time_two")

            #run five flows
            c,n1 = self.run_five(queue_size=100,use_fix=True)
            self.plot_rate_time([c[1].recvTime,c[3].recvTime,c[5].recvTime,c[7].recvTime,c[9].recvTime],
                [c[1].recvSize,c[3].recvSize,c[5].recvSize,c[7].recvSize,c[9].recvSize], "plot_rate_five")
            self.plot_window_time([c[0].windTime,c[2].windTime,c[4].windTime,c[6].windTime,c[8].windTime],
                [c[0].windSize,c[2].windSize,c[4].windSize,c[6].windSize,c[8].windSize], "window_time_five")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "queue_time_five")

            #without fix
            c,n1 = self.run_five(queue_size=100,use_fix=False)
            self.plot_rate_time([c[1].recvTime,c[3].recvTime,c[5].recvTime,c[7].recvTime,c[9].recvTime],
                [c[1].recvSize,c[3].recvSize,c[5].recvSize,c[7].recvSize,c[9].recvSize], "plot_rate_five_no_fix")
            self.plot_window_time([c[0].windTime,c[2].windTime,c[4].windTime,c[6].windTime,c[8].windTime],
                [c[0].windSize,c[2].windSize,c[4].windSize,c[6].windSize,c[8].windSize], "window_time_five_no_fix")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "queue_time_five_no_fix")
        
        if advanced_tests:
            #AIAD
            c1,c2,n1 = self.run(queue_size=50, additive_decrease=True)
            self.plot_rate_time([c2.recvTime],[c2.recvSize], "AIAD_rate_time")
            self.plot_window_time([c1.windTime],[c1.windSize], "AIAD_window_time")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "AIAD_queue_time")
            #AIMD - mult_const = 5/6
            c1,c2,c3,c4,n1 = self.run_two(queue_size=100, c1_mult_const=5.0/6.0,c3_mult_const=5.0/6.0)
            self.plot_rate_time([c2.recvTime,c4.recvTime],[c2.recvSize,c4.recvSize], "AIMD_plot_rate")
            self.plot_window_time([c1.windTime,c3.windTime],[c1.windSize,c3.windSize], "AIMD_window_time")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "AIMD_queue_time")
            #AIMD - mult_const = 1/2 & 5/6
            c1,c2,c3,c4,n1 = self.run_two(queue_size=100, c1_mult_const=1.0/2.0,c3_mult_const=5.0/6.0)
            self.plot_rate_time([c2.recvTime,c4.recvTime],[c2.recvSize,c4.recvSize], "unfair_plot_rate")
            self.plot_window_time([c1.windTime,c3.windTime],[c1.windSize,c3.windSize], "unfair_window_time")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "unfair_queue_time")
            #competing RTT
            c1,c2,c3,c4,n1,n2 = self.run_two_paths()
            self.plot_rate_time([c2.recvTime,c4.recvTime],[c2.recvSize,c4.recvSize], "competing_plot_rate")
            self.plot_window_time([c1.windTime,c3.windTime],[c1.windSize,c3.windSize], "competing_window_time")
            link_1 = n1.links[0]
            self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "competing_queue_1_time")
            
            link_2 = n2.links[2]
            self.plot_queue_time(link_2.queueTime,link_2.queueSize,link_2.dropTime,link_2.dropSize, "competing_queue_2_time")
            


if __name__ == '__main__':
    m = Main()

