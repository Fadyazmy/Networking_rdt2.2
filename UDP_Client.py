import binascii
import socket
import struct
import sys
import hashlib
import base64

# server configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
unpacker = struct.Struct('I I 8s 32s')
sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP


#packet sequence
curr_seq = 0
#packet acknowledgement
curr_ack = 0
#current data item being processed
data = ""




print("UDP target IP:", UDP_IP)
print("UDP target port:", UDP_PORT)

#DONE
def rdt_send(data):
    # Create the Checksum
    chksum = make_checksum(curr_ack, curr_seq,data )

    # gets the constructed UDP packet
    sndpkt = make_pkt(curr_ack, data, chksum)

    # send the UDP packet
    udt_send(sndpkt)

#DONE
def make_pkt(CURR_SEQ, data, chksum):
    #Build the UDP Packet
    values = (ackindex,curr_seq,base64.b64encode(data.encode('utf-8')),chksum)
    UDP_Packet_Data = struct.Struct('I I 8s 32s')
    UDP_Packet = UDP_Packet_Data.pack(*values)
    return UDP_Packet

#DONE
def udt_send(sndpkt):
    print('packet sent: ', sndpkt)
    # Send the UDP Packet to the server
    sock.sendto(sndpkt, (UDP_IP, UDP_PORT))


#DONE
def corrupt(rcvpkt):
    # Calculate new checksum of the  [ ACK, SEQ, DATA ]
    checksum = make_checksum(rcvpkt[0], rcvpkt[1], rcvpkt[2])
    # Compare calculated chechsum with checksum value in packet <-- NOT SURE ABOUT THIS
    if base64.b64encode(rcvpkt[3]) == checksum:
        print('CheckSums is OK')
        return False
    else:
        print('CheckSums Do Not Match')
        return True

def make_checksum(ACK, SEQ, DATA):
    values = (ACK, SEQ, DATA)
    packer = struct.Struct('I I 8s')
    packed_data = packer.pack(*values)
    checksum = base64.b64encode(hashlib.md5(packed_data).hexdigest().encode('utf-8'))
    return checksum

def isACK(rcvpkt, ACK_VALUE):
	#checks ACK is of value ACK_VALUE
    if rcvpkt[0] == ACK_VALUE and rcvpkt[1] == curr_seq:
        return True
    else:
        return False

def rdt_rcv(rcvpkt):
    global curr_ack
    global curr_seq
    global data_object

    # if the packet is not corrupted and is acknowledged, then adjust variables for next packet
    # otherwise resend packet
    if not corrupt(rcvpkt) and isACK(rcvpkt, curr_ack + 1):
        #Return TRUE for Client to send next packet
            curr_seq = (curr_seq+1)%2
            return True
    else:
        # packet corruption or no acknowledgement, resend the previous packet
        print('Invalid packet: ', rcvpkt)
        rdt_send(data_object)
        return False


data_list = ["NCC-1701", "NCC-1664", "NCC-1017"]

# send the data items in data_list consequetively
for data_object in data_list:
    success = False

    # send the data item util both sequences have been acknowledged by the server (success == True)
    while success == False:
        print('Data sent: ', data_object)
        # send the data item
        sock.settimeout(0)
        rdt_send(data_object)

        # Receive Data
        # sets the timeout duration for the packet listening function socket::recvfrom(...) at 9ms
        sock.settimeout(0.009)
        try:
            packet, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
        except socket.timeout:
            print('\nPacket timed out! Resending packet...\n\n')
            continue

        rcvpkt = unpacker.unpack(packet)
        print("received from: ", addr)
        print("received message: ", rcvpkt)
        success = rdt_rcv(rcvpkt)

        if success:
            print('rdt2.2 UDP Packet communication successful\n')