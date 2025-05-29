from scapy.all import *

response = sr1(IP(dst="8.8.8.8")/ ICMP(), timeout=2)

if response:
    response.show() 
