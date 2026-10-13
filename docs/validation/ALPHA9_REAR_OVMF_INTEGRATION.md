# Alpha9 — Plan de qualification ReaR + OVMF (sources officielles, 13 octobre 2026)

## Moteurs natifs, aucun pont supplémentaire
Harbor conserve les flux natifs Btrfs pour les sous-volumes en lecture seule,
ainsi que ses archives séparées pour les systèmes de fichiers EFI et /boot.
ReaR (Relax-and-Recover) doit prendre en charge le **layout des partitions**,
LUKS/LVM lorsque présent, le rescue ISO, /etc/fstab et les commandes de
réinstallation du chargeur ; le conteneur Qt ne réinvente aucun partitionneur.

## Deux modes officiels ReaR à qualifier en VM
- `OUTPUT=ISO` + `BACKUP=REQUESTRESTORE` : ReaR reconstruit partitions/montages,
  puis demande explicitement que l'outil externe restaure dans `/mnt/local`.
  Intégration initiale possible avec `harbor-checkpoint-v2 raw checkpoint-v2
  set-rear-recover` depuis un **rescue ISO réel**, jamais depuis l'OS courant.
- `OUTPUT=ISO` + `BACKUP=EXTERNAL` : ReaR peut intégrer `EXTERNAL_BACKUP`
  et `EXTERNAL_RESTORE`, mais l'issue 3523 a relevé un comportement où
  le programme externe n'était pas appelé. Ne **pas** considérer une
  configuration EXTERNAL comme certifiée sans voir la commande s'exécuter dans
  l'ISO de la version sélectionnée.

`rear mkrescue` construit un ISO sans recopier à tort tous les octets des
sauvegardes Harbor; `rear checklayout` détecte les changements nécessitant
un ISO actualisé. Sauvegarder ensemble l'ISO, l'inventaire du layout et
l'identifiant exact du jeu de volumes. Gérer les options `OUTPUT_URL`
conformément à la version ReaR: `OUTPUT_URL=null` n'est pas universel et
peut n'être autorisé qu'avec `BACKUP=NETFS`.

## Expérience OVMF exigée
1. Dans une VM UEFI au disque GPT vide : installation OS Linux sur ESP FAT32,
   root Btrfs, sous-volumes racine, home, var/log et un sous-volume imbriqué.
2. Capture `rear mkrescue`, catalogues Harbor checkpoint-v2 et vérification
   de chaque archive de données, boot et de l'inventaire.
3. **Effacement exclusivement du disque virtuel de test** et démarrage
   de l'ISO ReaR sous OVMF avec VARS indépendantes, aucune dépendance aux
   entrées EFI de Cloud9.
4. ReaR reconstruit partitionnement et mounts, puis Harbor restaure
   exclusivement dans `/mnt/local` en maintenant les UID/GID/xattrs/ACL;
   ReaR finalise l'initramfs et le bootloader.
5. Couper la VM, détacher le secours, démarrer **uniquement le disque récupéré**
   via OVMF, confirmer login, fstab, UUID, EFI, noyau, fichiers comparés.
6. Tester le cas où la partition EFI manque, où un sous-volume requis
   manque, une archive est corrompue, ou l'ISO ne correspond plus au layout:
   fail-closed, aucune annonce « bootable » prématurée.
7. Refaire au moins une incrémentale après le redémarrage récupéré.

## Sources web consultées le 13/10/2026
- Guide officiel ReaR : https://relax-and-recover.org/rear-user-guide/basics/configuration.html
- Issue correction EXTERNAL_RESTORE : https://relax-and-recover.org/rear-user-guide/issues/2025-09-24.3523.issue.closed.html
- ReaR commandes et limites BACKUP : https://github.com/rear/rear/blob/master/doc/rear.8.md
- ReaR `rear checklayout` : https://relax-and-recover.org/usage/
- Firmware OVMF : https://github.com/tianocore/edk2/blob/master/OvmfPkg/QEMU_PV_VARS.md

## Statut
**SPEC uniquement.** Aucun test de boot après restauration encore réalisé;
la GUI alpha9 ne lance que l'inventaire, la consultation de sets et la
prévisualisation du staging. Ne pas exposer de formatage de disque.
