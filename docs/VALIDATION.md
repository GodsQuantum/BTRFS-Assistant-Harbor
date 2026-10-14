# Matrice de validation de Btrfs Assistant Harbor 0.1.0-alpha9

**Checkpoint du 14 octobre 2026 — tests VM sur Cloud9, sans Pegasus ni disque de production.**

| Domaine | Preuve | Limite |
| --- | --- | --- |
| Rust CAS | 50 tests, format et Clippy strict | Pas de benchmark généraliste de production |
| Python | 39 tests | Cas simulés, pas toutes les configurations matérielles |
| Qt/UI | 5 CTests dont interactions sur le véritable widget de backup, en mode offscreen | Non équivalent à des essais manuels sur toutes les distributions |
| Btrfs | Envoi complet/incrémental, validation de chaînes et restauration en QEMU | Sur disques virtuels isolés |
| ReaR 2.9 + Harbor | **PASS R4** : ISO, disque vierge, GPT/ESP/Btrfs, restauration externe, GRUB standard et secours, reboot sans ISO, code retour 0 | Une racine Btrfs simple, EFI FAT32, GRUB, Secure Boot désactivé |
| NFS/SMB | Essais de connectivité/reprise en VM | Pas de certification GC destructif multi-clients |

Les preuves détaillées sont dans le dossier docs/validation/, notamment **QA_ALPHA9_REAR_GENERIC_HOOK_R4_20261014.md** et **QA_ALPHA9_UEFI_DISASTER_RECOVERY_R5_20261013.md**. Les logs et images volumineux demeurent dans le dossier de tests privé, hors Git.

## Ce qui n'est PAS certifié

- Matériel physique, fermetures/reprises de travail utilisateur sur Pegasus, Cloud9 ou autres postes.
- Secure Boot, chiffrement LUKS, LVM, RAID, multi-racines ou sous-volumes indépendants.
- Suppression CAS destructive sur NFS/SMB avec garanties de verrou multi-client.
- Tous les firmwares UEFI et tous les paquets de distributions.
- Une restauration universelle à un clic depuis la GUI.

Ne pas confondre la réussite du parcours testé avec une garantie universelle. Tout échec futur doit être consigné et corrigé avec reproduction avant de modifier le statut.
