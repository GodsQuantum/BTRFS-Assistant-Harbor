# Btrfs Assistant Harbor alpha9 — certification et livrables (14 octobre 2026)

## Certifié
- Fork Qt natif dans le worktree DEV700, branche `dev/alpha9-machine-recovery-20261013`.
- QEMU Alpine test `e2e_uefi_btrfs_disaster_recovery.py`: reconstruction scriptée disque GPT+ESP+Btrfs, Harbor CAS send+verify+receive et redémarrage sans ISO : PASS (R5).
- QEMU Debian 13 + ReaR 2.9: `rear mkrescue` dans le système source, ISO réel autonome (~706 Mio), boot OVMF sur disque vierge, `rear recover` recree GPT+ESP FAT32+Btrfs+swap, invoque un hook `BACKUP=EXTERNAL` **de laboratoire**, Harbor restaure racine et ESP, réinstalle automatiquement les binaires GRUB UEFI standard et secours (R2). Test R2: redémarrage sans ISO avec variables NVRAM créées lors de la récupération, Debian retrouve son fichier témoin. RC final 0.
- 14/10/2026: Python unittest **38 réussis**, CTest Qt **4/4**, Rust musl release tests réussis, Clippy strict et rustfmt `PASS`.
- CMake staging vérifié: `/usr/bin/harbor-transport`, `/usr/lib/btrfs-harbor/recovery/harbor-rear-restore`, `/usr/share/btrfs-harbor/rear/` présents.

## Limites bloquantes pour une version stable
- Le hook **générique du produit**, différent du hook QA qui a validé R2, est ajouté au fork mais **n'a pas encore passé un troisième parcours ISO ReaR → disque vierge → boot final**. Ne pas le qualifier `CERTIFIÉ` avant ce test.
- Le profil actuellement pris en charge est **un disque UEFI x86-64, une racine Btrfs, une ESP FAT32, GRUB, sans Secure Boot, sans LUKS, RAID ou montages de données distincts**. Pour tous les autres topologies, le hook doit refuser par défaut et ne pas écrire.
- Installateurs Arch/Fedora alpha9 et test d'installation sur un poste CachyOS (Pegasus) non terminés. L'alpha9 Debian compilée et contrôlée n'a pas été installée en production.
- Un seul paquet logiciel ne remplace pas les sauvegardes originales. Ne pas promettre restauration des configurations Snapper réelles ou CAS GC destructif NFS/SMB.

## État et sécurité
- Pas de modification de `main`, pas de tag `stable` ni nouvelle release GitHub stable.
- Ne pas toucher aux montages/NFS/ACL, Snapper, disques de Cloud9, ou Pegasus.
- Répertoire projet: `/srv/storage/cloud/arezki/Projets/HomeLab/BTRFS Harbor/`. Lab ReaR jetable: `qa-vm-rear-alpha9/`; ne pas supprimer les logs/ISOs R2 avant la livraison définitive.
- Candidate Debian de travail (pas installé): `/home/arezki/Dev/harbor-alpha9-qa/btrfs-assistant-harbor_0.1.0~alpha9-1_amd64.deb`.
- **Pour la suite** : générer une ISO ReaR intégrant le *hook du produit*, certifier le parcours R3 sur disque totalement neuf et vérifier les deux chemins UEFI, compléter les paquets Arch/deb/rpm et un vrai smoke test graphique sur VM, puis seulement publier les releases officiellement stables.
