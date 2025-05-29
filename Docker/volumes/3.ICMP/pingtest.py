from scapy.all import *

ip = IP(dst="8.8.8.8")

icmp = ICMP ()

pkt = ip / icmp

reply = sr1 (pkt)
print("ICMP reply ..........")

print("Source IP : ", reply[IP].src)
print("Destination IP :", reply[IP].dst)
