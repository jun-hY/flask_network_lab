import sys
from scapy.all import *

print("SENDING ICMP PACKET..............")
a = IP()

a.dst = '93.184.216.34'
b = ICMP()

for TTL in range(1,20):
  a.ttl = TTL
  h = sr1(a/b, timeout=2, verbose=0)
  if h is None:
      print("Router: *** (hops = {})".format(TTL))
  else:
      print("Router: {} (hops = {})".format(h.src, TTL))
