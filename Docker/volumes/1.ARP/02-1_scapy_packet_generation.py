from scapy.all import *

pkt = Ether()/IP(dst="8.8.8.8")/TCP(dport=80)/Raw(load="GET / HTTP/1.1\r\n\r\n")
pkt.show()
