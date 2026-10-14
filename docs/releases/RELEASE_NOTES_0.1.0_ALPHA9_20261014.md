# Version 0.1.0-alpha9 (rev. 2) — 14 octobre 2026

**Livraison de préversion vérifiée en VM, pas certification universelle de matériel.**

## Livré
- Fork Qt natif de Btrfs Assistant 2.3.2 préservant Snapper, sous-volumes, restauration et maintenance locale.
- Deux moteurs séparés : Harbor checkpoint-v2 historique et CAS Rust (FastCDC/BLAKE3/zstd, chaînes Btrfs complètes et incrémentales, vérification, staging de reprise).
- Rétention CAS sur plan confirmé avec préservation des archives parents, simulation par défaut et refus du GC destructif réseau non certifié.
- Interface « Remote backups » plus accessible sur les petits écrans grâce à un défilement vertical, avec sélection d'archives, programmation, reprise, prévisualisation et messages d'état.
- Intégration ReaR 2.9 **opt-in**, avec réparation automatique du GRUB EFI standard et de secours et refus des topologies non couvertes.
- Documentation Git repensée, guides FR/EN, tests de sécurité ReaR, tests de parcours GUI.
- Scripts de construction des paquets et stockage des builds/logs **hors Git**.

## Preuves
- 50 tests Rust, 39 tests Python et 5 CTest Qt, dont 4 scénarios d'interaction avec le véritable widget de sauvegarde.
- Vraie restauration ReaR 2.9 sur QEMU Debian 13 : ISO autonome → disque GPT/ESP/Btrfs vierge → Harbor CAS → deux GRUB EFI → démarrage sans ISO et vérification des données, code retour zéro.
- Chemin ReaR testé uniquement sur UEFI x86-64, une racine Btrfs, une ESP FAT32, GRUB et Secure Boot désactivé.

## Limites
Pas de garantie sur Secure Boot, RAID/LUKS/LVM, multi-sous-volumes indépendants, toutes distributions et firmwares, sauvegardes personnelles réelles, ni GC destructif multi-client NFS/SMB. Le jeu de backup reste sous contrôle de l'administrateur.

## Mise à jour
Conserver une sauvegarde indépendante et les paramètres Snapper. Installer en parallèle avec le logiciel officiel ; tester le paquet et la restauration sur une VM avant matériel. Les chemins ReaR d'exemple sont fournis sous /usr/share/btrfs-harbor/rear, sans modifier /etc/rear/local.conf.

Tests : voir docs/VALIDATION.md et docs/validation/QA_ALPHA9_REAR_GENERIC_HOOK_R4_20261014.md.
