# Matrice de validation de Btrfs Assistant Harbor 0.1.0-alpha9

## Certification candidate au 16 octobre 2026 (prioritaire sur le tableau historique ci-dessous)

| Porte | Preuve sur le code candidat | Restriction |
| --- | --- | --- |
| Rust / Python / Qt | 53 tests Rust, rustfmt et Clippy strict RC0 ; 47 tests Python RC0 ; 6 CTest Qt RC0 | Les tests ne remplacent pas le terrain |
| Debian 13 | Paquet alpha9-8, UEFI/Btrfs Debian13 : upgrade rev7→8→7→8 puis purge, GUI FR X11/125%, invité et QEMU RC0 | Ubuntu, KDE/Wayland non certifiés |
| Fedora 44 | VM UEFI/Btrfs, RPM rev2→rev7→rev2→rev7→supprimé : RC0 | RPM rev8 construit avec CTest6/6 et Rust PASS en conteneur Fedora, mais cycle VM rev8 non refait |
| Arch Linux 2026-10-15 | VM UEFI/Btrfs, paquet rev2→rev7→rev2→rev7→supprimé : RC0 | Arch rev8 makepkg interrompu à 100% d'occupation NVMe ; rev7 VM PASS, rev8/CachyOS non certifiés |
| CAS local | 3 exécutions complètes/incrémentales et restauration, CAS GC local ; SIGKILL durant envoi puis reprise vérifiée sur vraie VM Btrfs | Coupure VM/powerloss et GC réseau à certifier séparément |
| NFS | Serveur + 2 clients QEMU, exclusivité flock NFSv4 PASS | local_lock=flock dangereux/inconclusif, GC réseau strictement refusé |
| SMB | SMB3 : deux clients Linux distincts, verrou exclusif et réacquisition après libération PASS ; préflight et coupure en plein transfert, reprise CAS, vérification et réception des données PASS | GC destructif SMB strictement refusé ; diversité de serveurs non certifiée |
| ReaR 2.9 | R8 : ISO, disque vierge, UEFI, GPT, Btrfs, ESP, GRUB double, reboot sans ISO PASS | Une racine simple, Secure Boot désactivé |

Rapports détaillés : [Checkpoint R26 du 16 octobre](validation/QA_ALPHA9_R26_CHECKPOINT_2026-10-16.md), [GUI et i18n](validation/QA_ALPHA9_GUI_FR_CANDIDATE_2026-10-15.md), [Fedora/Arch/NFS](validation/QA_ALPHA9_FEDORA_ARCH_NFS_2026-10-16.md) et [ReaR R8](validation/QA_ALPHA9_REAR_R8_2026-10-15.md). Les logs réels et SHA des paquets sont conservés dans le workspace QA NVMe hors Git.

**La version stable n'est pas autorisée : l'espace NVMe est saturé, les packages rev8 Fedora/Arch et les portes G10/G15/G22/G23 ne sont pas tous certifiés.** Les fonctionnalités non démontrées (GC réseau destructif, Secure Boot, LUKS/LVM/RAID, système multi-volumes et systemd-boot) doivent rester refusées par défaut.


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
