import sys
sys.path.append('..')

from src.sim import Sim
from src import node
from src import link
from src import packet

from networks.network import Network

import random

class DelayHandler(object):

    def receive_packet(self,packet):
        print Sim.scheduler.current_time(),"\t",packet.ident,"\t",packet.created,"\t",\
            Sim.scheduler.current_time() - packet.created,packet.transmission_delay,"\t",\
            packet.propagation_delay,"\t",packet.queueing_delay

class DelayHandler3Node():
    def __init__(self):
        self.count = 0

    def receive_packet(self,packet):
        self.count += 1
        if self.count == 1000:
            print "End Time:", Sim.scheduler.current_time()
            print "Queueing delay:", packet.queueing_delay

_1MBPS = 1000000
_1GBPS = _1MBPS * 1000

def run():
    print "time\t","ident\t","created\t", "sent_at\t", "Dtrans\t", "Dprop\t", "Dqueue\t"
    Sim.scheduler.run()

def twoNodeSetUp():
    # parameters
    Sim.scheduler.reset()

    # setup network
    net = Network('twoNodes.txt')

    # setup routes
    n1 = net.get_node('n1')
    n2 = net.get_node('n2')
    n1.add_forwarding_entry(address=n2.get_address('n1'),link=n1.links[0])
    n2.add_forwarding_entry(address=n1.get_address('n2'),link=n2.links[0])

    # setup app
    d = DelayHandler()
    net.nodes['n2'].add_protocol(protocol="delay",handler=d)
    
    
    return n1,n2

"""
Set the bandwidth of the links to 1 Mbps, with a propagation delay of 1 second. 
Send one packet with 1000 bytes from n1 to n2 at time 0.
"""
def twoNodes_1():
    n1,n2 = twoNodeSetUp()

    n1.links[0].bandwidth = _1MBPS
    n2.links[0].bandwidth = _1MBPS
    n1.links[0].propagation = 1;
    n2.links[0].propagation = 1;

    # send one packet
    p = packet.Packet(destination_address=n2.get_address('n1'),
                        ident=1,protocol='delay',length=1000)
    Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)
    # run the simulation
    run()

"""
Set the bandwidth of the links to 100 bps, with a propagation delay of 10 ms. 
Send one packet witih 1000 bytes from n1 to n2 at time 0.
"""
def twoNodes_2():
    n1,n2 = twoNodeSetUp()

    n1.links[0].bandwidth = 100
    n2.links[0].bandwidth = 100
    n1.links[0].propagation = 0.010 #10 ms
    n2.links[0].propagation = 0.010 #10 ms

    # send one packet
    p = packet.Packet(destination_address=n2.get_address('n1'),
                        ident=1,protocol='delay',length=1000)
    Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)

    run()



"""
Set the bandwidth of the links to 1 Mbps, with a propagation delay of 10 ms. 
Send three packets from n1 to n2 at time 0 seconds, then one packet at time 2 seconds. 
All packets should have 1000 bytes.
"""
def twoNodes_3():
    n1,n2 = twoNodeSetUp()

    n1.links[0].bandwidth = _1MBPS
    n2.links[0].bandwidth = _1MBPS
    n1.links[0].propagation = 0.010 #10 ms
    n2.links[0].propagation = 0.010 #10 ms

    # send three packet
    p = packet.Packet(destination_address=n2.get_address('n1'),
                        ident=1,protocol='delay',length=1000)
    Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)
    p = packet.Packet(destination_address=n2.get_address('n1'),
                        ident=1,protocol='delay',length=1000)
    Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)
    p = packet.Packet(destination_address=n2.get_address('n1'),
                        ident=1,protocol='delay',length=1000)
    Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)

    #One more at t=2
    p = packet.Packet(destination_address=n2.get_address('n1'),
                        ident=1,protocol='delay',length=1000)
    Sim.scheduler.add(delay=2, event=p, handler=n1.send_packet)

    run()

def threeNodeSetup():
    # parameters
    Sim.scheduler.reset()

    # setup network
    net = Network('threeNodes.txt')

    # setup routes
    n1 = net.get_node('n1')
    n2 = net.get_node('n2')
    n3 = net.get_node('n3')
    n1.add_forwarding_entry(address=n2.get_address('n1'),link=n1.links[0])
    n1.add_forwarding_entry(address=n3.get_address('n2'),link=n1.links[0])
    n2.add_forwarding_entry(address=n1.get_address('n2'),link=n2.links[0])
    n2.add_forwarding_entry(address=n3.get_address('n2'),link=n2.links[1])
    n3.add_forwarding_entry(address=n1.get_address('n2'),link=n3.links[0])
    n3.add_forwarding_entry(address=n2.get_address('n3'),link=n3.links[0])

    # setup app
    d = DelayHandler3Node()
    net.nodes['n3'].add_protocol(protocol="delay",handler=d)
    
    return n1,n2,n3

#def sendPacket(src, dest):


"""
Two fast links - 1MBPS - 100ms

Node A transmits a stream of 1 kB packets to node C. 
How long does it take to transfer a 1 MB file, divided into 1 kB packets, from A to C? 
Which type of delay dominates?
"""
def fastLinks():
    n1,n2,n3 = threeNodeSetup()

    n1.links[0].bandwidth = _1MBPS
    n2.links[0].bandwidth = _1MBPS
    n2.links[1].bandwidth = _1MBPS
    n3.links[0].bandwidth = _1MBPS

    n1.links[0].propagation = 0.100 #100 ms
    n2.links[0].propagation = 0.100 #100 ms
    n2.links[1].propagation = 0.100 #100 ms
    n3.links[0].propagation = 0.100 #100 ms



    for i in range(0,1000):
        p = packet.Packet(destination_address=n3.links[0].address,
                        ident=i,protocol='delay',length=1000)
        Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)

    Sim.scheduler.run()

"""
If both links are upgraded to a rate of 1 Gbps, how long does it take to transfer a 1 MB file from A to C?
"""
def fasterLinks():
    n1,n2,n3 = threeNodeSetup()

    n1.links[0].bandwidth = _1GBPS
    n2.links[0].bandwidth = _1GBPS
    n2.links[1].bandwidth = _1GBPS
    n3.links[0].bandwidth = _1GBPS

    n1.links[0].propagation = 0.100 #100 ms
    n2.links[0].propagation = 0.100 #100 ms
    n2.links[1].propagation = 0.100 #100 ms
    n3.links[0].propagation = 0.100 #100 ms

    for i in range(0,1000):
        p = packet.Packet(destination_address=n3.links[0].address,
                        ident=i,protocol='delay',length=1000)
        Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)

    Sim.scheduler.run()
"""
One fast link and one slow link - 1MBPS/256KBPS - 100ms

Node A transmits 1000 packets, each of size 1 kB, to node C. 
How long would it does it take to transfer a 1 MB file, divided into 1 kB packets, from A to C?
"""
def slowLink():
    n1,n2,n3 = threeNodeSetup()

    n1.links[0].bandwidth = _1MBPS
    n2.links[0].bandwidth = _1MBPS
    n2.links[1].bandwidth = 256*1000 #256Kbps
    n3.links[0].bandwidth = 256*1000 #256Kbps

    n1.links[0].propagation = 0.100 #100 ms
    n2.links[0].propagation = 0.100 #100 ms
    n2.links[1].propagation = 0.100 #100 ms
    n3.links[0].propagation = 0.100 #100 ms

    for i in range(0,1000):
        p = packet.Packet(destination_address=n3.links[0].address,
                        ident=i,protocol='delay',length=1000)
        Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)
    Sim.scheduler.run()


def testlink():
    net = Network('threeNodes.txt')

    # setup routes
    n1 = net.get_node('n1')
    n2 = net.get_node('n2')
    n3 = net.get_node('n3')

    n1.add_forwarding_entry(address=n2.get_address("n1"),link=n1.links[0])
    n1.add_forwarding_entry(address=n3.get_address("n2"),link=n1.links[0])
    n2.add_forwarding_entry(address=n1.get_address("n2"),link=n2.links[0])
    n2.add_forwarding_entry(address=n3.get_address("n2"),link=n2.links[1])
    n3.add_forwarding_entry(address=n1.get_address("n2"),link=n3.links[0])
    n3.add_forwarding_entry(address=n2.get_address("n3"),link=n3.links[0])

    # setup app
    d = DelayHandler()
    net.nodes['n3'].add_protocol(protocol="delay",handler=d)

    for i in range(0,1000):
        p = packet.Packet(destination_address=n3.links[0].address,
                        ident=i,protocol='delay',length=1000)
        Sim.scheduler.add(delay=0, event=p, handler=n1.send_packet)

    Sim.scheduler.run()

if __name__ == '__main__':
    print
    print "Two nodes Scenerios" 
    print
    print "1MBPS bandwidth - Dprop 1 sec - one 1000 byte packet"
    twoNodes_1()
    print 
    print "100bps bandwidth - Dprop 10 ms - one 1000 byte packet"
    twoNodes_2()
    print 
    print "1Mbps bandwidth - Dprop 10 ms - three 1000 byte packet, one more at t=2"
    twoNodes_3()
    print
    print "Three node Scenerios"
    print
    print "Fast Links"
    fastLinks()
    print 
    print "Faster Links"
    fasterLinks()
    print
    print "Fast/Slow Links"
    slowLink()




