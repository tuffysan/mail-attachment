# Proxmox LXC installation

## Installation med en rad

Kör som `root` på Proxmox-värden:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh)"
```

Installationsscriptet:

1. verifierar Proxmox-kommandon och storage;
2. väljer nästa lediga LXC-ID;
3. hämtar senaste Debian 12-template;
4. skapar en unprivilegierad LXC;
5. aktiverar Docker-kompatibla LXC-inställningar;
6. installerar Docker och Docker Compose;
7. klonar Mail Attachment Hub;
8. genererar säkra hemligheter och adminlösenord;
9. bygger och startar tjänsterna;
10. väntar på `/health/ready`;
11. installerar administrationskommandot `mailhub`;
12. visar URL och inloggningsuppgifter.

## Standardresurser

- 2 CPU-kärnor
- 4096 MB RAM
- 512 MB swap
- 24 GB disk
- DHCP på `vmbr0`
- applikationsstorage `local-lvm`
- template-storage `local`

## Anpassad installation

```bash
CTID=134 MEMORY_MB=6144 CORES=4 DISK_GB=40 ADMIN_EMAIL=admin@example.com TZ=Europe/Stockholm bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh)"
```

## Statisk IP

```bash
IPV4=192.168.1.50/24 GATEWAY=192.168.1.1 DNS_SERVER=192.168.1.1 bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh)"
```

## Annan storage

Kontrollera först:

```bash
pvesm status
```

Ange sedan storage:

```bash
STORAGE=local-lvm TEMPLATE_STORAGE=local bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh)"
```

## Efter installation

```bash
pct enter <CTID>
```

Tillgängliga kommandon:

```bash
mailhub status
mailhub logs
mailhub restart
mailhub stop
mailhub start
mailhub update
mailhub backup
mailhub restore <backup-directory>
mailhub doctor
mailhub credentials
```

Adminuppgifterna finns i:

```text
/root/mailhub-credentials.txt
```

Applikationen finns i:

```text
/opt/mail-attachment-hub
```

## Felet "can't find file local:vztmpl"

Installeraren skriver loggmeddelanden till stderr. Därför innehåller
templatevariabeln endast det riktiga templatefilnamnet och inte loggtext.

Exempel på korrekt templatevärde:

```text
debian-12-standard_12.12-1_amd64.tar.zst
```

## Thin pool-varning

Varningen:

```text
Sum of all thin volume sizes exceeds the size of thin pool
```

betyder att thin-poolen är överallokerad. Installationen kan fortsätta om
det finns verkligt ledigt utrymme, men kontrollera:

```bash
pvesm status
lvs
```
