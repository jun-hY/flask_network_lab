from scapy.all import *

packets = sniff(count=10)

for pkt in packets:
    pkt.show()
