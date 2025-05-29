from scapy.all import *

def packet_callback (pkt):
    if pkt.haslayer(ICMP):
        print("ICMP detected") 
        pkr.show()

sniff(filter="icmp", prn=packet_callback, count=5)
