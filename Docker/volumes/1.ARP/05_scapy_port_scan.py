from scapy.all import *

target_ip = "10.9.0.5"
ports = [22, 80, 443]

for port in ports:
    print("scanning port :", port)
    pkt = IP(dst=target_ip) / TCP(dport=port, flags="S")
    resp = sr1(pkt, timeout=1, verbose=0)

    if resp and resp.haslayer(TCP) and resp[TCP].flags == 0x12:
        print(f"Port {port} is open")
