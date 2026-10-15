# Btrfs Assistant Harbor

**Fork de Btrfs Assistant 2.3.2** intégrant les sauvegardes distantes Snapper, un moteur CAS Rust et une récupération UEFI avec ReaR.

[Guide utilisateur](docs/guides/UTILISATION_FR.md) · [Récupération de machine](docs/guides/RECUPERATION_REAR_FR.md) · [Tests et limites](docs/VALIDATION.md) · [Développement](docs/DEVELOPMENT.md) · [English](README.md)

> **0.1.0-alpha9 — préversion, pas version stable universelle.** La restauration complète a réussi sur des **disques virtuels QEMU**, pas sur tous les ordinateurs physiques. Conserver une sauvegarde indépendante et vérifiée. Btrfs Assistant officiel et Snapper ne sont pas remplacés.

## Fonctions

| Fonction | Disponible | Limite |
| --- | --- | --- |
| Btrfs et Snapper | Snapshots locaux, retour arrière, sous-volumes, maintenance, navigation | Snapper garde le contrôle des snapshots |
| Checkpoint v2 | Compatibilité Harbor historique, transferts interrompus, planification | Format distinct du CAS |
| Harbor CAS | Rust, FastCDC/BLAKE3, zstd, sauvegarde Btrfs complète/incrémentale, vérification de chaîne, staging | Snapshot source Btrfs en lecture seule et dépôt dédié |
| Rétention CAS | Plan de simulation, confirmation par empreinte, conservation des parents et blocs partagés | Suppression destructive interdite par défaut sur NFS/SMB |
| ReaR 2.9 | ISO UEFI, reconstruction GPT/Btrfs/ESP, restauration CAS et réparation automatique des deux chargeurs GRUB | Une racine Btrfs simple, ESP FAT32, UEFI x86-64, Secure Boot désactivé |

L'onglet **Remote backups** rassemble les sources Snapper, la destination, les envois, l'inventaire, la vérification, la prévisualisation de récupération, la programmation et la rétention. Les archives des deux moteurs **ne sont pas interchangeables**.

## Compiler sans écraser le système

Prérequis : C++17, Qt6 Widgets/LinguistTools, CMake, Ninja, Rust/Cargo, libbtrfsutil, Python 3 et btrfs-progs. Snapper et polkit sont nécessaires aux opérations courantes.

    git clone https://github.com/GodsQuantum/BTRFS-Assistant-Harbor.git
    cd BTRFS-Assistant-Harbor
    cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
    cmake --build build --parallel 4
    QT_QPA_PLATFORM=offscreen ctest --test-dir build --output-on-failure
    DESTDIR="$PWD/staging" cmake --install build

Inspecter le résultat dans **staging/**. Installer ensuite uniquement un paquet compatible vérifié. Ne pas remplacer le paquet officiel Btrfs Assistant.

**Compatibilité paquets, constat du 15 octobre 2026 :** le paquet DEB alpha9 révision 2 publié sur GitHub exige `libqt6core6t64 >= 6.10.2`, alors que Debian 13 (Trixie) fournit officiellement Qt 6.8.2. Une installation dans une VM Debian 13 a échoué (`apt` RC=100). Ne pas forcer l'installation ni abaisser artificiellement les dépendances : un paquet **recompilé et testé sur Debian 13** reste nécessaire. La restauration Debian 13 via ReaR en ISO a été testée séparément ; elle ne prouve pas la compatibilité du paquet GUI DEB. Ubuntu 26.04, Fedora et Arch doivent encore passer de vrais tests d'installation/upgrade/désinstallation. L'application se lance depuis le menu du bureau ; le CLI CAS dispose de **harbor-transport --help**.

## Première sauvegarde, sans confusion

1. Créer ou sélectionner un **snapshot Snapper en lecture seule**.
2. Ouvrir **Remote backups**, choisir la configuration Snapper et son snapshot.
3. Choisir checkpoint-v2 (ancien dépôt) **ou** CAS (nouveau dépôt dédié). Pour CAS, cliquer **Initialize CAS destination** dans un répertoire existant et vide.
4. Lancer **Send selected snapshot**, puis **List remote backups** et **Verify selected archive**.
5. Pour tester la récupération, choisir un staging **Btrfs neuf et vide**, différent de la racine du système, et utiliser **Preview recovery**.
6. Avant une suppression CAS, contrôler le plan de simulation et confirmer seulement le plan attendu ; ne pas forcer le GC destructif sur NFS/SMB.

Voir [le guide utilisateur détaillé](docs/guides/UTILISATION_FR.md).

## Récupération d'un système entier

**Preuve en VM Debian 13 / ReaR 2.9** : ISO créée depuis la machine source, nouveau disque 7 GiB GPT + ESP FAT32 + Btrfs, restauration externe de la racine via Harbor, reconstruction automatique des deux GRUB EFI, démarrage Debian **sans ISO** avec vérification du noyau, de l'ESP et des données.

Il ne s'agit pas d'un bouton de formatage dans la GUI. Le script de secours est **facultatif**, installé comme composant mais jamais activé automatiquement dans /etc/rear. Chaque machine réelle nécessite sa propre qualification : [guide ReaR](docs/guides/RECUPERATION_REAR_FR.md).

## État des tests et avertissements

**50 tests Rust, 39 tests Python, 5 CTest/Qt**, y compris une interaction avec le véritable onglet de sauvegardes en mode sans affichage ; essais complets Btrfs et ReaR en QEMU. [Matrice détaillée](docs/VALIDATION.md).

**Non certifié :** Secure Boot, LUKS/LVM/RAID, plusieurs racines/sous-volumes indépendants, suppression CAS sur NFS/SMB avec verrouillage distribué, tout matériel et tous paquets des distributions. Ne jamais considérer un test VM comme une garantie universelle.

## Organisation

- **src/** interface native Qt et fonctions Btrfs/Snapper ;
- **transport/** moteur Rust CAS ;
- **backend/** outils de compatibilité, planification et secours ReaR ;
- **vendor/harbor-legacy/** ancien moteur sous licence séparée ;
- **tests/** non-régression et interface ;
- **packaging/** distribution ;
- **docs/guides/** utilisation et reprise ;
- **docs/validation/** preuves ;
- **docs/archive/** historique.

Fork indépendant de [Btrfs Assistant officiel](https://gitlab.com/btrfs-assistant/btrfs-assistant), sous GPL-3.0-or-later avec composants tiers identifiés. [Licence](LICENSE).
