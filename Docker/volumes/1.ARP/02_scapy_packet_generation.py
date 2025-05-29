from scapy.all import *

packet = IP(dst="192.168.1.1") / TCP(dport=80, flags="S")
packet.show()
