import sys
sys.path.append('..')

from src.sim import Sim
from src.connection import Connection
from src.tcppacket import TCPPacket
from src.buffer import SendBuffer,ReceiveBuffer

class TCP(Connection):
    ''' A TCP connection between two hosts.'''
    def __init__(self,transport,source_address,source_port,
                 destination_address,destination_port,app=None,window=1000,
                 dyn_timer=False, threshold=100000, lossPackets=[], reno=False,
                 additive_decrease=False, mult_const=0.5, use_fix=True):
        Connection.__init__(self,transport,source_address,source_port,
                            destination_address,destination_port,app)

        self.reno = reno
        self.dyn_timer = dyn_timer
        self.additive_decrease = additive_decrease
        self.mult_const = mult_const
        self.use_fix = use_fix

        ### Sender functionality
        # maximum segment size, in bytes
        self.mss = 1000
        #default threshold window size for conguestion control is 100000
        self.threshold = threshold
        # send window; represents the total number of bytes that may
        # be outstanding at one time
        self.window = self.mss
        #ackCount is used to track Acks in Additive increase
        self.ackCount = 0
        #lastAck keeps track of the last ack to be recieved.
        self.lastAck = -1
        #dupAckCount keeps track of the number of times a duplicate ack is recieved
        self.dupAckCount = 0
        #lossPackets is a array of packet indexes, telling the process which one to drop.
        self.lossPackets = lossPackets

        # send buffer
        self.send_buffer = SendBuffer() 
        
        # largest sequence number that has been ACKed so far; represents
        # the next sequence number the client expects to receive
        self.sequence = 0
        # retransmission timer
        self.timer = None
        # timeout duration in seconds
        self.timeout = 1.0
        #minimum timeout duration in seconds
        self.timeout_min = .2
        self.timeout_max = 2
        #tracks packet sent times 
        self.sent_time = {}
        self.alpha = 0.125

        #This is a hack to try and fix the multiple dropped packets before
        self.lastWindowSeq = 0
        self.lastLossWindowSeq = 0

        #keep track of timeout history
        #this is used for lab 2
        self.timeout_hist = []
        #keep track of sent/lost/ack times and sequence nums
        #used for lab 3 graphs
        self.sentTime = []
        self.sentSeq = []
        self.lostTime = []
        self.lostSeq = []
        self.ackTime = []
        self.ackSeq = []
        #used for lab 4 graphs
        self.windTime = []
        self.windSize = []



        ### Receiver functionality

        # receive buffer
        self.receive_buffer = ReceiveBuffer()
        # ack number to send; represents the largest in-order sequence
        # number not yet received
        self.ack = 0

        #used for lab 4 graphs
        self.recvTime = []
        self.recvSize = []

    def trace(self,message):
        ''' Print debugging messages. '''
        #Sim.trace("TCP",message)
        

    def receive_packet(self,packet):
        ''' Receive a packet from the network layer. '''
        if packet.ack_number > 0:
            # handle ACK
            self.handle_ack(packet)
        if packet.length > 0:
            # handle data
            self.handle_data(packet)

    ''' Sender '''

    def send(self,data):
        ''' Send data on the connection. Called by the application. This
            code currently sends all data immediately. 
            Change this code to send individual packets in the current window.
            Maximum packet size of 1000 bytes
            Sequence numbers count bytes
            '''
        self.send_buffer.put(data)
        self.send_availible()

    def send_availible(self):
        """sends any availible data without going past the window restriction"""
        sequence = 0
        while self.send_buffer.available() > 0 and self.send_buffer.outstanding() < self.window:
            #send up to the window limit
            size = self.window - self.send_buffer.outstanding()
            #print "window,out",self.window,self.send_buffer.outstanding()
            if size > self.mss:
                size = self.mss
            data,sequence = self.send_buffer.get(size)
            #print "size,seq",size,sequence
            self.send_packet(data,sequence)
        #if you just filled the window, then save the last packet sequence. 
        if self.send_buffer.outstanding() >= self.window:
            self.lastWindowSeq = sequence

    def send_packet(self,data,sequence):
        if sequence in self.lossPackets:
            self.lossPackets.remove(sequence)
            self.lostTime.append(Sim.scheduler.current_time())
            self.lostSeq.append(sequence)
        else:
            self.sentTime.append(Sim.scheduler.current_time())
            self.sentSeq.append(sequence)
            packet = TCPPacket(source_address=self.source_address,
                               source_port=self.source_port,
                               destination_address=self.destination_address,
                               destination_port=self.destination_port,
                               body=data,
                               sequence=sequence,ack_number=0)
            # send the packet
            self.trace("%s (%d) sending TCP segment to %d for %d" % \
                (self.node.hostname,self.source_address,self.destination_address,packet.sequence))
            self.trace("%s timeout %f" % \
                (self.node.hostname,self.timeout))
            self.sent_time[packet.sequence] = Sim.scheduler.current_time()
            self.transport.send_packet(packet)
        #set the timer
        self.set_timer()
        
    def handle_ack(self,packet):
        ''' 
            Handle an incoming ACK. 
            Remove acked data from the window, if it is at the front
            Send any addition data allowed by the new window.
            Reset timer? (this happens whenever something is sent already)
        '''
        if self.sequence < packet.ack_number:
            self.sequence = packet.ack_number
        #adjust send buffer
        self.send_buffer.slide(self.sequence)
        #measure RTO
        rto = Sim.scheduler.current_time() - self.sent_time[packet.sequence]

        #save the time and sequence for lab 3
        self.ackTime.append(Sim.scheduler.current_time())
        self.ackSeq.append(packet.ack_number)

        #we have gotten farther than the last loss event
        if self.lastLossWindowSeq + self.mss < packet.ack_number:
            self.lastLossWindowSeq = 0

        #note the check for lastlossWindowSeq requires that window size is evenly divisable by self.mss
        if self.lastAck == packet.ack_number:
            self.dupAckCount +=1
            if self.dupAckCount == 3 and (self.lastLossWindowSeq + self.mss != packet.ack_number or self.use_fix == False):
                self.lastLossWindowSeq = self.lastWindowSeq
                print "windowSeq: ,", self.lastWindowSeq
                print "Three dup acks ", self.lastAck
                self.cancel_timer();
                self.retransmit(None);
            #ignore any and all duplicate acks, don't look to transmit more data.
            return
        else:
            self.lastAck = packet.ack_number
            self.adjustWindow()
            self.dupAckCount = 0

        self.timeout = (1-self.alpha) * self.timeout + self.alpha*rto
        if self.timeout < self.timeout_min:
            self.timeout = self.timeout_min

        #uncomment this line for project 2 graphs.
        #self.timeout_hist.append(self.timeout)

        self.send_availible()
        if self.send_buffer.outstanding() <= 0: #not waiting on anything.
            self.cancel_timer() 
        
    #handles adjusting the window each time a ACK is recieved
    def adjustWindow(self):
        #adjust window size
        if self.window >= self.threshold:
            if self.ackCount >= float(self.window)/self.mss:
                self.window += self.mss
                self.threshold += self.mss
                self.ackCount = 0
            else:
                self.ackCount += 1
        else:
            self.window += self.mss
        self.windTime.append(Sim.scheduler.current_time()) 
        self.windSize.append(self.window)

    def lossEvent(self):
        #self.dupAckCount = 0 #not sure if I need this
        if self.additive_decrease:
            self.threshold = max(self.window - self.mss,self.mss)
        else:
            self.threshold = max(self.window * self.mult_const,self.mss)
        #slow start
        if self.reno:
            self.window = max(self.window * self.mult_const,self.mss)
        else:
            self.window = self.mss
        self.windTime.append(Sim.scheduler.current_time()) 
        self.windSize.append(self.window)


    def retransmit(self,event):
        ''' 
            Retransmit data. 
            Timer has expired
            Only send the first packet in the window.
            Forget other packets
        '''
        if not event is None:
            print "Timer Expired"
        self.timer = None
        self.trace("%s (%d) retransmission timer fired" % (self.node.hostname,self.source_address))
        self.timeout = self.timeout*2
        if self.timeout > self.timeout_max:
            self.timeout = self.timeout_max
        
        #uncomment this line for project 2 graphs.
        #self.timeout_hist.append(self.timeout)
        self.lossEvent()
        
        data,sequence = self.send_buffer.resend(self.mss)
        self.send_packet(data, sequence)


    def set_timer(self):
        '''sets or resets the timer'''
        self.cancel_timer()
        if not self.dyn_timer:
            self.timeout = 1
        self.timer = Sim.scheduler.add(delay=self.timeout, event='retransmit', handler=self.retransmit)

    def cancel_timer(self):
        ''' Cancel the timer. '''
        if not self.timer:
            return
        Sim.scheduler.cancel(self.timer)
        self.timer = None

    ''' Receiver '''

    def handle_data(self,packet):
        ''' Handle incoming data. This code currently gives all data to
            the application, regardless of whether it is in order, and sends
            an ACK.
            Change this code to store packets regardless of order 
            and only give them (in order) to the app when all packets are recieved.
            '''
        self.trace("%s (%d) received TCP segment from %d for %d" % (self.node.hostname,packet.destination_address,packet.source_address,packet.sequence))
        
        self.receive_buffer.put(packet.body,packet.sequence)
        data,start = self.receive_buffer.get()
        #set the ack to the next sequence needed.
        ack = start + len(data)
        curTime = Sim.scheduler.current_time()
        if curTime in self.recvTime:
            self.recvSize[len(recvSize)] += len(data)*8
        else:
            self.recvTime.append(curTime)
            self.recvSize.append(len(data)*8)

        self.app.receive_data(data,packet)
        self.send_ack(ack,packet.sequence)

    def send_ack(self, ack, sequence):
        ''' 
        Send an ack. 
        This ack should be the highest consecutive packet recieved up to this point.

        '''
        packet = TCPPacket(source_address=self.source_address,
                           source_port=self.source_port,
                           destination_address=self.destination_address,
                           destination_port=self.destination_port,
                           sequence=sequence,ack_number=ack)
        # send the packet
        self.trace("%s (%d) sending TCP ACK to %d for %d" % (self.node.hostname,self.source_address,self.destination_address,packet.ack_number))
        self.transport.send_packet(packet)
