# ⚓ Configuration et restauration

[← Accueil](../README.fr.md) · [Technical details](TECHNICAL.fr.md)

## 🛟 Un snapshot local ne remplace pas une sauvegarde

Snapper permet de revenir sur une modification. Mais **un snapshot présent sur le même disque ne protège pas contre une panne de ce disque**. Harbor conserve les fonctions de [Btrfs Assistant](https://gitlab.com/btrfs-assistant/btrfs-assistant) et ajoute le transfert de snapshots Btrfs en lecture seule, leur vérification et la restauration en zone de préparation, jamais directement à la place de la racine active.

| | Ce que permet Harbor |
|---|---|
| 🧭 **Gestion Btrfs et Snapper** | Snapshots locaux, sous-volumes et retour arrière dans l'interface native Qt 6. |
| 📦 **Sauvegardes distantes** | Envois Btrfs complets et incrémentaux, vérification et destination NFS dédiée. |
| 🧩 **Dépôt CAS commun** | Un unique `Workstations/`, un seul pool de blocs, des manifestes distincts par machine. |
| ♻️ **Reprise et rétention** | Transferts interrompus, inventaire, contrôle d'intégrité et aperçu avant suppression. **GC destructif NFS/SMB interdit.** |
| 🔎 **Restauration prudente** | Réception dans un nouveau dossier Btrfs vide, puis vérification avant toute intervention sur le système. |
| 🌍 **Interface multilingue** | English, français et 简体中文. |

<p align="center"><img src="../branding/workflow.svg" alt="Du snapshot Snapper vers un dépôt CAS partagé, puis vers une restauration préparée" width="880"></p>

## 📥 Installation

Télécharge le paquet **Linux x86-64** correspondant à ton système depuis les [Releases GitHub](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/releases/latest) : **Arch/CachyOS** (`.pkg.tar.zst`), **Debian 13** (`.deb`) ou **Fedora 44** (`.rpm`). Vérifie `SHA256SUMS` avant installation.

Sur Arch/CachyOS, depuis le dossier contenant les fichiers téléchargés :

```bash
sha256sum -c SHA256SUMS
sudo pacman -U ./btrfs-assistant-harbor-*-x86_64.pkg.tar.zst
```

Lance ensuite **Btrfs Assistant Harbor** depuis KDE. L'application s'installe **à côté de Btrfs Assistant**, sans le supprimer ni modifier les configurations Snapper.

## 🚀 Première sauvegarde vers Cloud9 ou un NAS

1. Dans **Sauvegardes distantes**, choisis la configuration Snapper et un snapshot **en lecture seule** déjà créé.
2. Sélectionne le moteur **Harbor CAS** et le dossier de sauvegarde **réellement monté en NFS**. Vérifie le montage pour éviter toute écriture dans un dossier local de remplacement.
3. Clique une seule fois sur **Initialiser la destination CAS** à la racine commune `Workstations/`. Le dépôt crée `.harbor-repo-id`, `objects/` et `machines/<nom>/manifests/`. Le nom de machine est modifiable.
4. Lance **Envoyer le snapshot sélectionné**, puis **Lister les sauvegardes distantes** et **Vérifier l'archive sélectionnée**. Les autres postes Linux peuvent partager le même pool.
5. Teste une restauration **dans un nouveau dossier Btrfs vide**, en conservant une sauvegarde indépendante tant que la récupération de ta machine n'a pas été éprouvée.

Le moteur interdit volontairement le **garbage collection destructif sur NFS/SMB/SSHFS/9p** : ne contourne pas cette protection. Les anciennes archives **checkpoint-v2** et CAS ne sont pas interchangeables.

## ✅ Certifié pour un périmètre Linux précis

La [certification Linux 0.1.0](validation/QA_LINUX_STABLE_SCOPE_2026-10-22.md) couvre Rust/Clippy, Qt/Python, Snapper réel sur Btrfs, deux invités Linux QEMU avec sauvegarde/restauration, annulation d'un vrai `btrfs send`, concurrence CAS, 1 000 cycles et tests des paquets natifs. Chaque nouvelle version doit passer sa propre CI.

**Non pris en charge :** capture macOS/APFS native ; suppression destructive CAS sur stockage réseau ; récupération ReaR avec Secure Boot, LUKS/LVM/RAID ou plusieurs racines. La récupération ReaR facultative n'a été validée que sur UEFI/GRUB, ESP FAT32, une racine Btrfs et Secure Boot désactivé. Les coupures électriques physiques et toutes les configurations matérielles ne sont pas certifiées.

## 🧰 Développement

Prérequis : C++17, CMake, Ninja, Qt 6 Widgets/Test/LinguistTools, libbtrfsutil, btrfs-progs, Rust/Cargo et Python 3.

```bash
git clone https://github.com/GodsQuantum/BTRFS-Assistant-Harbor.git
cd BTRFS-Assistant-Harbor
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
cmake --build build --parallel 4
QT_QPA_PLATFORM=offscreen ctest --test-dir build --output-on-failure
cargo test --locked --manifest-path transport/Cargo.toml --all-targets
```

Voir [Contribution](../CONTRIBUTING.md), [Sécurité](../SECURITY.md), [Charte visuelle](../branding/BRAND.md), [documentation ReaR](guides/RECUPERATION_REAR_FR.md) et [Issues](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/issues).

**Crédits et licence :** fork indépendant de **Btrfs Assistant**, sous **GPL-3.0-or-later**, sans affiliation ni validation de l'équipe upstream. Le composant Python Harbor historique dispose de ses propres mentions MIT. Voir [LICENSE](../LICENSE) et les licences tierces.
