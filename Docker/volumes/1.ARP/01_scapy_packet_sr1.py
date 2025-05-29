from scapy.all import *

pkt = IP(dst="8.8.8.8")/ICMP()

resp = sr1(pkt, timeout=2)

if resp:
   resp.show()
