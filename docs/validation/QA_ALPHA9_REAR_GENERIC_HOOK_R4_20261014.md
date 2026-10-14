# Alpha9 — ReaR 2.9 + Harbor : certification du script distribué (R4)
Date : **14 octobre 2026**. Cible : VM jetable Debian 13, x86_64, GPT + ESP FAT32 + racine Btrfs, GRUB, sans Secure Boot.

## Test R4 du code réellement fourni
- Script sous test : `backend/recovery/harbor-rear-restore`, installé sous `/usr/lib/btrfs-harbor/recovery/harbor-rear-restore`. Hash de ce fichier dans la source et dans l'ISO ReaR R4 : `af83295faa845836c0df678587a8662c73de737d484ba9f243218a013b1c40a9`.
- VM source : Debian 13 démarrée en UEFI sur root Btrfs. ReaR 2.9 `mkrescue` a construit `qa-vm-rear-alpha9/share/rear-product-r4.iso` (SHA256 `c229ea8278114882be47cc68d0e05deaef411e5d118df4dfed7029b039439141`). Le CLI Harbor natif, le manifeste CAS, l'archive EFI, le profil root-owned et le script distribué étaient tous présents dans l'ISO.
- **Nouvelle VM R4** : `recovered-debian-product-r4.raw`, sparse, exactement 7GiB, créé VIERGE dans le laboratoire avec variables OVMF nouvelles. Aucune autre cible de données que `/dev/vda`; ISO en lecture seule.
- Boot ISO ReaR → `rear -v recover` → ReaR crée lui-même GPT, ESP VFAT (`vda1`), racine Btrfs (`vda2`) et swap (`vda3`), puis invoque `BACKUP=EXTERNAL` vers le script du produit.
- **Code retour de rear recover = 0** : `HARBOR_PRODUCT_R4_REAL_REAR_RECOVER_RC:0`; marqueur restauré valide, les deux chargeurs EFI reconstruits dans la racine /mnt/local. Les empreintes SHA256 des deux fichiers sont identiques : `5263b51d325c20726ed7ecd88ba973867d302da5ce5d1487ce56f4b7efab4884`. Les deux journaux `/var/log/harbor-rear-grub-standard.log` et `...-fallback.log` contiennent `Installation finished. No error reported.`.
- Arrêt du secours, suppression **de l'ISO au démarrage** (VM ne présente que le disque restauré) et réutilisation des mêmes variables UEFI que pendant `rear recover`. Debian 13 a démarré automatiquement sans réinstallation GRUB manuelle : `HARBOR_PRODUCT_R4_REAL_REAR_UEFI_BTRFS_NO_ISO_BOOT_RC:0` ; `findmnt` donne `/dev/vda2 btrfs`, `/dev/vda1 vfat`, et le marqueur original `HARBOR_REAR_ROOT_QA_20261013` a été retrouvé. Noyau et initramfs originaux présents.

## Régression R3 corrigée
L'ISO précédente R3 échouait volontairement en fail-closed avec `UNSAFE_ESP_ARCHIVE` parce que la validation refusait `./` dans les listes tar normales. Le script R4 accepte les chemins normaux `./EFI/...` mais continue à rejeter les chemins absolus et les traversées `../`. Test de sécurité automatisé : `test_esp_archive_accepts_normal_dot_prefix_and_rejects_traversal`, PASS.

## Périmètre et limites
**Certifié en VM uniquement :** un disque UEFI x86_64 avec racine Btrfs simple, ESP FAT32 et GRUB, sans Secure Boot. Cela ne qualifie ni RAID/LUKS/Secure Boot, ni sous-volumes ou systèmes de fichiers indépendants, ni tous les firmwares matériels. La procédure est opt-in et **ne configure pas /etc/rear/local.conf** lors de l'installation. CAS GC destructif sur NFS/SMB demeure refusé par défaut.

Les images ISO et journaux R1–R4 sont gardés dans le dossier privé canonique `/srv/storage/cloud/arezki/Projets/HomeLab/BTRFS Harbor/qa-vm-rear-alpha9/`. La version stable du logiciel n'a pas été annoncée : les tests d'installation et GUI spécifiques aux différents systèmes cibles restent séparés. Le branchement et le tag de préversion doivent correspondre à cette preuve.
