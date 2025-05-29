from scapy.all import *


ether1 = Ether(dst = "ff:ff:ff:ff:ff:ff")
arp1 = ARP(pdst="10.9.0.5")
frame1 = ether1/arp1
sendp(frame1)

arp1.show()
