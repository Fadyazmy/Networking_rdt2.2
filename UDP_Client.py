import binascii
import socket
import struct
import sys
import hashlib
import base64
import time

# server configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 5006
unpacker = struct.Struct('I I 8s 32s')
sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

# packet sequence
curr_seq = 0
# packet acknowledgement
curr_ack = 0
# current data item being processed
data = ""

print("UDP target IP:", UDP_IP)
print("UDP target port:", UDP_PORT)


# DONE
def rdt_send(data_obj):
    global curr_seq, curr_ack

    # Create the Checksum
    values = (curr_ack, curr_seq, base64.b64encode(data_obj.encode('utf-8')))
    UDP_Data = struct.Struct('I I 8s')
    packed_data = UDP_Data.pack(*values)
    chksum = hashlib.md5(packed_data).hexdigest().encode('utf-8')


    # gets the constructed UDP packet
    sndpkt = make_pkt(curr_ack, data_obj, chksum)

    # send the UDP packet
    udt_send(sndpkt)

def make_checksum(ACK, SEQ, DATA):
    values = (ACK, SEQ, DATA)
    packer = struct.Struct('I I 8s')
    packed_data = packer.pack(*values)
    checksum = hashlib.md5(packed_data).hexdigest().encode('utf-8')
    return checksum

# DONE
def make_pkt(curr_ack, data, chksum):
    global curr_seq

    # Build the UDP Packet
    values = (curr_ack, curr_seq,  base64.b64encode(data.encode('utf-8')), chksum)
    UDP_Packet_Data = struct.Struct('I I 8s 32s')
    UDP_Packet = UDP_Packet_Data.pack(*values)
    return UDP_Packet


# DONE
def udt_send(sndpkt):
    print('packet sent: ', sndpkt)
    # Send the UDP Packet to the server
    sock.sendto(sndpkt, (UDP_IP, UDP_PORT))


# DONE
def corrupt(rcvpkt):
    # Calculate new checksum of the  [ ACK, SEQ, DATA ]
    checksum = make_checksum(rcvpkt[0], rcvpkt[1], rcvpkt[2])
    # Compare calculated chechsum with checksum value in packet <-- NOT SURE ABOUT THIS
    if rcvpkt[3] == checksum:
        print('CheckSums is OK')
        return False
    else:
        print('CheckSums Do Not Match')
        return True



def isACK(rcvpkt, ACK_VALUE):
    global curr_seq, curr_ack
    # checks ACK is of value ACK_VALUE
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
        # Return TRUE for Client to send next packet
        curr_seq = (curr_seq + 1) % 2
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
        # send the data item
        sock.settimeout(0)
        rdt_send('b' + data_object)
        print('Data sent: ', data_object)

        # Receive Data
        # sets the timeout duration for the packet listening function socket::recvfrom(...) at 9ms
        sock.settimeout(0.009)
        try:
            packet, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
        except socket.timeout:
            print('Packet timed out! Resending packet...\n\n')
            continue

        rcvpkt = unpacker.unpack(packet)
        print("received from: ", addr)
        print("received message: ", rcvpkt)
        success = rdt_rcv(rcvpkt)

        if success:
            print('rdt2.2 UDP Packet communication successful\n')

