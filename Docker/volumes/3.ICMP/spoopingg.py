# 공격자(10.9.0.111)에서 패킷 캡처
from scapy.all import *

def monitor(pkt):
    if IP in pkt:
        print(pkt.summary())

sniff(filter="ip", prn=monitor)

