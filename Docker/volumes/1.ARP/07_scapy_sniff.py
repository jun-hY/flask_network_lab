from scapy.all import *

def http_filter(pkt):
    if pkt.haslayer(Raw) and b"GET" in pkt[Raw].load:
        print("HTTP GET detected")
        pkt.show()

sniff(filter="tcp port 80", prn=http_filter, count=5)
