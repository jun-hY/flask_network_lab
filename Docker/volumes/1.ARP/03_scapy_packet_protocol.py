from scapy.all import *

icmp_packet = IP(dst="8.8.8.8") / ICMP()

udp_packet = IP(dst="8.8.8.8") / UDP(dport=53)

arp_packet = ARP(pdst="192.168.1.1")

icmp_packet.show()
udp_packet.show()
arp_packet.show()
