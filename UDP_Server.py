import binascii
import socket
import struct
import sys
import hashlib
import base64

UDP_IP = "127.0.0.1"
UDP_PORT = 5006

# Integer, Integer, 8 letter char array, 32 letter char array
unpacker = struct.Struct('I I 8s 32s')

# Create the socket and listen
sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP
sock.bind((UDP_IP, UDP_PORT))


def make_pkt(CURR_ACK, CURR_SEQ, data, chksum):
    # Build the UDP Packet
    values = (CURR_ACK, CURR_SEQ, data, chksum)
    UDP_Packet_Data = struct.Struct('I I 8s 32s')
    UDP_Packet = UDP_Packet_Data.pack(*values)
    return UDP_Packet


def make_checksum(ACK, SEQ, DATA):
    values = (ACK, SEQ, DATA)
    packer = struct.Struct('I I 8s')
    packed_data = packer.pack(*values)
    checksum = hashlib.md5(packed_data).hexdigest().encode('utf-8')
    return checksum


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


while True:
    print("Listening")
    # Receive Data
    data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
    UDP_Packet = unpacker.unpack(data)
    print("received from:", addr)
    print("received message:", UDP_Packet)

    # Compare Checksums to test for corrupt data
    if not corrupt(UDP_Packet):
        print('CheckSums Match, Packet OK')

        # Built checksum [ACK, SEQ, DATA]
        ACK = UDP_Packet[0] + 1
        SEQ = UDP_Packet[1]
        DATA = b''
        chksum = make_checksum(ACK, SEQ, DATA)

        # Build the UDP Packet [CURR_ACK, CURR_SEQ, data, chksum]
        UDP_Packet = make_pkt(UDP_Packet[0] + 1, UDP_Packet[1], b'', chksum)
        print('Packeting')

        # Send the UDP Packet
        sock.sendto(UDP_Packet, addr)
        print('Sent')
    else:
        print('Checksums Do Not Match, Packet Corrupt')

        # Built checksum [ACK, SEQ, DATA]
        chksum = make_checksum(UDP_Packet[0] + 1, (UDP_Packet[1] + 1) % 2, b'')

        # Build the UDP Packet [CURR_ACK, CURR_SEQ, data, chksum]
        UDP_Packet = make_pkt(UDP_Packet[0] + 1, (UDP_Packet[1] + 1) % 2, b'', chksum)
        print('Packeting')

        # Send the UDP Packet
        sock.sendto(UDP_Packet, addr)
        print('Sent')
