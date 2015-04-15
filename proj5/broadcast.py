import sys
sys.path.append('..')

from src.sim import Sim
from src import node
from src import link
from src import packet
from src.transport import Transport
from src.tcp import TCP

from networks.network import Network

import random

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

class BroadcastApp(object):
    def __init__(self,node):
        self.node = node
        #send a broadcast packet every 30 seconds
        Sim.scheduler.add(delay=0, event=None, handler=self.broadcast)
        node.init_vector_table()
        self.run = True

    def broadcast(self,event):
        self.node.decrement_TTL()
        body = ["DV"]
        body.extend(self.node.get_vector_table_msg())
        p = packet.Packet(source_address=self.node.get_address('X'),destination_address=0,
                            ident=2,ttl=1,protocol='broadcast',length=100, body=body)
        Sim.scheduler.add(delay=0, event=p, handler=self.node.send_packet)
        if self.run:
            Sim.scheduler.add(delay=30, event=None, handler=self.broadcast)

    def receive_packet(self,packet):
        #print "node,",self.node.hostname ,"body,", packet.body
        if isinstance(packet.body,list) and packet.body[0] == "DV":
            self.node.update_vector_table(packet.body[1:])
        else:
            print packet.destination_address
            #if packet.destination_address in self.node.links:
            print "node,",self.node.hostname ,"body,", packet.body

class PacketApp(object):

    def receive_packet(self,packet):
        print "Packet body:", packet.body

class Main(object):
    def __init__(self):
        self.broadcastApps = []
        self.color = ["black","blue","yellow","green","orange"]

    def end_test(self,event):
        for app in self.broadcastApps:
            print app.node.get_vector_table_msg()
            app.run = False

    def print_vector_tables(self,Message):
        print Message
        for app in self.broadcastApps:
            print app.node.get_vector_table_msg()

    def use_TCP(self):
        print "FIFTEEN_NODE_MESH_EXPERIMENT"
        # parameters
        Sim.scheduler.reset()
        Sim.set_debug(True)
        #Sim.debug = {"Node":True}

        # setup network
        net = Network('../networks/fifteen-nodes.txt')

        # get nodes
        nodes = []
        nodes.append(net.get_node('n1'))
        nodes.append(net.get_node('n2'))
        nodes.append(net.get_node('n3'))
        nodes.append(net.get_node('n4'))
        nodes.append(net.get_node('n5'))
        nodes.append(net.get_node('n6'))
        nodes.append(net.get_node('n7'))
        nodes.append(net.get_node('n8'))
        nodes.append(net.get_node('n9'))
        nodes.append(net.get_node('n10'))
        nodes.append(net.get_node('n11'))
        nodes.append(net.get_node('n12'))
        nodes.append(net.get_node('n13'))
        nodes.append(net.get_node('n14'))
        nodes.append(net.get_node('n15'))

        for node in nodes:
            b = BroadcastApp(node)
            p = PacketApp()
            node.add_protocol(protocol="broadcast",handler=b)
            node.add_protocol(protocol="packet",handler=p)
            self.broadcastApps.append(b)
        
        # setup transport
        t1 = Transport(nodes[0])
        t2 = Transport(nodes[12])
        filename = "internet-architecture.pdf"
        a = AppHandler(filename)

        c1 = TCP(t1,nodes[0].get_address('n4'),1,nodes[12].get_address('n5'),1,a,use_fix=True)
        c2 = TCP(t2,nodes[12].get_address('n5'),1,nodes[0].get_address('n4'),1,a,use_fix=True)

       

        # send a file
        with open(filename,'r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=200, event=data, handler=c1.send)

        Sim.scheduler.add(delay=1000, event=None, handler=self.end_test)


        # run the simulation
        Sim.scheduler.run()
        self.broadcastApps = []


        self.plot_rate_time([c2.recvTime],[c2.recvSize], "plot_rate_one")
        self.plot_window_time([c1.windTime],[c1.windSize], "window_time_one")
        link_1 = nodes[0].get_link('n4')
        self.plot_queue_time(link_1.queueTime,link_1.queueSize,link_1.dropTime,link_1.dropSize, "queue_time_one")
        


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
        xlim([199,0.6])
        ylim([-5,55])

        savefig('%s.png' % filename)

    def plot_rate_time(self, recvTimeList, recvSizeList, filename):
        clf()
        figure(figsize=(15,5))
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
        plt.gca().set_xlim(left=199, right=205)
        savefig('%s.png' % filename)

    def plot_window_time(self, windTimeList, windSizeList, filename):
        clf()
        figure(figsize=(15,5))
        for i in range(0,len(windTimeList)):
            plot(windTimeList[i],windSizeList[i],color=self.color[i])
        xlabel('Time (seconds)')
        ylabel('window size (bytes)')
        plt.gca().set_xlim(left=199, right=205)
        savefig('%s.png' % filename)

    def plot_queue_time(self, queueTime, queueSize, dropTime, dropSize, filename):
        clf()
        figure(figsize=(15,5))
        scatter(queueTime,queueSize,marker='s',s=3)
        scatter(dropTime,dropSize,marker='x',color='black')
        xlabel('Time (seconds)')
        ylabel('Queue Size (# of packets)')
        plt.gca().set_xlim(left=199, right=205)
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

    def counting_to_infinity(self):
        print "COUNTING_TO_INFINITY_EXPERIMENT"
        # parameters
        Sim.scheduler.reset()
        Sim.set_debug(True)
        #Sim.debug = {"Node":True}

        # setup network
        net = Network('../networks/five-node-row.txt')

        # get nodes
        n1 = net.get_node('n1')
        n2 = net.get_node('n2')
        n3 = net.get_node('n3')
        n4 = net.get_node('n4')
        n5 = net.get_node('n5')

        # setup broadcast application
        b1 = BroadcastApp(n1)
        p1 = PacketApp()
        n1.add_protocol(protocol="broadcast",handler=b1)
        n1.add_protocol(protocol="packet",handler=p1)
        b2 = BroadcastApp(n2)
        p2 = PacketApp()
        n2.add_protocol(protocol="broadcast",handler=b2)
        n2.add_protocol(protocol="packet",handler=p2)
        b3 = BroadcastApp(n3)
        p3 = PacketApp()
        n3.add_protocol(protocol="broadcast",handler=b3)
        n3.add_protocol(protocol="packet",handler=p3)
        b4 = BroadcastApp(n4)
        p4 = PacketApp()
        n4.add_protocol(protocol="broadcast",handler=b4)
        n4.add_protocol(protocol="packet",handler=p4)
        b5 = BroadcastApp(n5)
        p5 = PacketApp()
        n5.add_protocol(protocol="broadcast",handler=b5)
        n5.add_protocol(protocol="packet",handler=p5)

        self.broadcastApps.extend([b1,b2,b3,b4,b5])


        
        Sim.scheduler.add(delay=150, event="Before Link Drops", handler=self.print_vector_tables)
        Sim.scheduler.add(delay=149, event=None, handler=n1.get_link('n2').down)
        Sim.scheduler.add(delay=149, event=None, handler=n2.get_link('n1').down)
        Sim.scheduler.add(delay=245, event="After 1", handler=self.print_vector_tables)
        Sim.scheduler.add(delay=335, event="After 2", handler=self.print_vector_tables)
        Sim.scheduler.add(delay=515, event="After 3", handler=self.print_vector_tables)

        Sim.scheduler.add(delay=700, event=None, handler=self.end_test)

        # run the simulation
        Sim.scheduler.run()
        self.broadcastApps = []
    
    def fifteen_node_mesh(self):
        print "FIFTEEN_NODE_MESH_EXPERIMENT"
        # parameters
        Sim.scheduler.reset()
        Sim.set_debug(True)
        #Sim.debug = {"Node":True}

        # setup network
        net = Network('../networks/fifteen-nodes.txt')

        # get nodes
        nodes = []
        nodes.append(net.get_node('n1'))
        nodes.append(net.get_node('n2'))
        nodes.append(net.get_node('n3'))
        nodes.append(net.get_node('n4'))
        nodes.append(net.get_node('n5'))
        nodes.append(net.get_node('n6'))
        nodes.append(net.get_node('n7'))
        nodes.append(net.get_node('n8'))
        nodes.append(net.get_node('n9'))
        nodes.append(net.get_node('n10'))
        nodes.append(net.get_node('n11'))
        nodes.append(net.get_node('n12'))
        nodes.append(net.get_node('n13'))
        nodes.append(net.get_node('n14'))
        nodes.append(net.get_node('n15'))

        for node in nodes:
            b = BroadcastApp(node)
            p = PacketApp()
            node.add_protocol(protocol="broadcast",handler=b)
            node.add_protocol(protocol="packet",handler=p)
            self.broadcastApps.append(b)
        
        p = packet.Packet(destination_address=nodes[4].get_address('n4'),
                        ident=1,protocol='packet',length=1000, body="FAILURE")
        Sim.scheduler.add(delay=200, event=p, handler=nodes[0].send_packet)

        Sim.scheduler.add(delay=280, event=None, handler=nodes[0].get_link('n4').down)
        Sim.scheduler.add(delay=280, event=None, handler=nodes[3].get_link('n1').down)

        p = packet.Packet(destination_address=nodes[4].get_address('n4'),
                        ident=3,protocol='packet',length=1000, body="SUCCESS")
        Sim.scheduler.add(delay=600, event=p, handler=nodes[0].send_packet)


        Sim.scheduler.add(delay=700, event=None, handler=nodes[0].get_link('n4').up)
        Sim.scheduler.add(delay=700, event=None, handler=nodes[3].get_link('n1').up)

        p = packet.Packet(destination_address=nodes[4].get_address('n4'),
                        ident=4,protocol='packet',length=1000, body="SUCCESS")

        Sim.scheduler.add(delay=900, event=p, handler=nodes[0].send_packet)


        Sim.scheduler.add(delay=1000, event=None, handler=self.end_test)

        # run the simulation
        Sim.scheduler.run()
        self.broadcastApps = []

    def five_node_row(self):
        print "FIVE_NODE_ROW_EXPERIMENT"
        # parameters
        Sim.scheduler.reset()
        Sim.set_debug(True)
        #Sim.debug = {"Node":True}

        # setup network
        net = Network('../networks/five-node-row.txt')

        # get nodes
        n1 = net.get_node('n1')
        n2 = net.get_node('n2')
        n3 = net.get_node('n3')
        n4 = net.get_node('n4')
        n5 = net.get_node('n5')

        # setup broadcast application
        b1 = BroadcastApp(n1)
        p1 = PacketApp()
        n1.add_protocol(protocol="broadcast",handler=b1)
        n1.add_protocol(protocol="packet",handler=p1)
        b2 = BroadcastApp(n2)
        p2 = PacketApp()
        n2.add_protocol(protocol="broadcast",handler=b2)
        n2.add_protocol(protocol="packet",handler=p2)
        b3 = BroadcastApp(n3)
        p3 = PacketApp()
        n3.add_protocol(protocol="broadcast",handler=b3)
        n3.add_protocol(protocol="packet",handler=p3)
        b4 = BroadcastApp(n4)
        p4 = PacketApp()
        n4.add_protocol(protocol="broadcast",handler=b4)
        n4.add_protocol(protocol="packet",handler=p4)
        b5 = BroadcastApp(n5)
        p5 = PacketApp()
        n5.add_protocol(protocol="broadcast",handler=b5)
        n5.add_protocol(protocol="packet",handler=p5)

        self.broadcastApps.extend([b1,b2,b3,b4,b5])
        
        p = packet.Packet(destination_address=n5.get_address('n4'),
                        ident=1,protocol='packet',length=1000, body="FAILURE")
        Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)

        p = packet.Packet(destination_address=n5.get_address('n4'),
                        ident=3,protocol='packet',length=1000, body="SUCCESS")
        Sim.scheduler.add(delay=300, event=p, handler=n1.send_packet)

        Sim.scheduler.add(delay=400, event=None, handler=self.end_test)

        # run the simulation
        Sim.scheduler.run()
        self.broadcastApps = []

    def five_node_loop(self):
        print "FIVE_NODE_LOOP_EXPERIMENT"
        # parameters
        Sim.scheduler.reset()
        Sim.set_debug(True)
        #Sim.debug = {"Node":True}

        # setup network
        net = Network('../networks/five-node-loop.txt')

        # get nodes
        n1 = net.get_node('n1')
        n2 = net.get_node('n2')
        n3 = net.get_node('n3')
        n4 = net.get_node('n4')
        n5 = net.get_node('n5')

        # setup broadcast application
        b1 = BroadcastApp(n1)
        p1 = PacketApp()
        n1.add_protocol(protocol="broadcast",handler=b1)
        n1.add_protocol(protocol="packet",handler=p1)
        b2 = BroadcastApp(n2)
        p2 = PacketApp()
        n2.add_protocol(protocol="broadcast",handler=b2)
        n2.add_protocol(protocol="packet",handler=p2)
        b3 = BroadcastApp(n3)
        p3 = PacketApp()
        n3.add_protocol(protocol="broadcast",handler=b3)
        n3.add_protocol(protocol="packet",handler=p3)
        b4 = BroadcastApp(n4)
        p4 = PacketApp()
        n4.add_protocol(protocol="broadcast",handler=b4)
        n4.add_protocol(protocol="packet",handler=p4)
        b5 = BroadcastApp(n5)
        p5 = PacketApp()
        n5.add_protocol(protocol="broadcast",handler=b5)
        n5.add_protocol(protocol="packet",handler=p5)
        
        self.broadcastApps.extend([b1,b2,b3,b4,b5])

        p = packet.Packet(destination_address=n5.get_address('n4'),
                        ident=1,protocol='packet',length=1000, body="n1->n5")
        Sim.scheduler.add(delay=180, event=p, handler=n1.send_packet)
        """
        p = packet.Packet(destination_address=n3.get_address('n2'),
                        ident=2,protocol='packet',length=1000, body="n5->n3")
        Sim.scheduler.add(delay=210, event=p, handler=n5.send_packet)

        p = packet.Packet(destination_address=n3.get_address('n2'),
                        ident=3,protocol='packet',length=1000, body="n2->n3")
        Sim.scheduler.add(delay=240, event=p, handler=n2.send_packet)

        p = packet.Packet(destination_address=n4.get_address('n5'),
                        ident=4,protocol='packet',length=1000, body="n1->n4")
        Sim.scheduler.add(delay=270, event=p, handler=n1.send_packet)
        """
        Sim.scheduler.add(delay=279, event=None, handler=self.print_vector_tables)

        Sim.scheduler.add(delay=280, event=None, handler=n1.get_link('n5').down)
        Sim.scheduler.add(delay=280, event=None, handler=n5.get_link('n1').down)

        #try sending those packets again to see difference in the path
        p = packet.Packet(destination_address=n5.get_address('n4'),
                        ident=1,protocol='packet',length=1000, body="n1->n5")
        Sim.scheduler.add(delay=600, event=p, handler=n1.send_packet)
        """
        p = packet.Packet(destination_address=n3.get_address('n2'),
                        ident=2,protocol='packet',length=1000, body="n5->n3")
        Sim.scheduler.add(delay=630, event=p, handler=n5.send_packet)

        p = packet.Packet(destination_address=n3.get_address('n2'),
                        ident=3,protocol='packet',length=1000, body="n2->n3")
        Sim.scheduler.add(delay=660, event=p, handler=n2.send_packet)

        p = packet.Packet(destination_address=n4.get_address('n5'),
                        ident=4,protocol='packet',length=1000, body="n1->n4")
        Sim.scheduler.add(delay=690, event=p, handler=n1.send_packet)
        """
        Sim.scheduler.add(delay=700, event=None, handler=self.end_test)
        # run the simulation
        Sim.scheduler.run()

        self.broadcastApps = []

    def run(self):
        # parameters
        Sim.scheduler.reset()
        Sim.set_debug(True)

        # setup network
        net = Network('../networks/five-nodes.txt')

        # get nodes
        n1 = net.get_node('n1')
        n2 = net.get_node('n2')
        n3 = net.get_node('n3')
        n4 = net.get_node('n4')
        n5 = net.get_node('n5')

        # setup broadcast application
        b1 = BroadcastApp(n1)
        n1.add_protocol(protocol="broadcast",handler=b1)
        b2 = BroadcastApp(n2)
        n2.add_protocol(protocol="broadcast",handler=b2)
        b3 = BroadcastApp(n3)
        n3.add_protocol(protocol="broadcast",handler=b3)
        b4 = BroadcastApp(n4)
        n4.add_protocol(protocol="broadcast",handler=b4)
        b5 = BroadcastApp(n5)
        n5.add_protocol(protocol="broadcast",handler=b5)


        # send a broadcast packet from 1 with TTL 2, so everyone should get it
        # p = packet.Packet(source_address=n1.get_address('n2'),destination_address=0,ident=1,ttl=2,protocol='broadcast',length=100)
        # Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)

        # # send a broadcast packet from 1 with TTL 1, so just nodes 2 and 3
        # # should get it
        # p = packet.Packet(source_address=n1.get_address('n2'),destination_address=0,ident=2,ttl=1,protocol='broadcast',length=100)
        # Sim.scheduler.add(delay=1, event=p, handler=n1.send_packet)

        # # send a broadcast packet from 3 with TTL 1, so just nodes 1, 4, and 5
        # # should get it
        # p = packet.Packet(source_address=n3.get_address('n1'),destination_address=0,ident=3,ttl=1,protocol='broadcast',length=100)
        # Sim.scheduler.add(delay=2, event=p, handler=n3.send_packet)

        # run the simulation
        Sim.scheduler.run()

if __name__ == '__main__':
    m = Main()
    #m.five_node_row()
    #m.five_node_loop()
    #m.fifteen_node_mesh()
    m.counting_to_infinity()
    #m.use_TCP()
