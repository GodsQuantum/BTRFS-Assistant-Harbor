# Btrfs Assistant Harbor

**Périmètre de production Linux 0.1.0 (candidat en certification, 22 octobre 2026) :**
Btrfs Assistant Harbor vise **Linux x86-64 avec Btrfs et Snapper**, avec des paquets natifs Debian 13, Fedora 44 et Arch/CachyOS. Sauvegardes CAS et restaurations sont testées sur de vrais volumes Btrfs jetables et dans des invités Linux QEMU. La restauration doit cibler **un nouveau répertoire Btrfs de préparation vide**, sans écrasement automatique du système en cours. ReaR reste facultatif et limité à UEFI/GRUB, ESP FAT32, racine Btrfs unique et Secure Boot désactivé. GC destructif NAS, restauration chiffrée/multi-racine et **macOS/APFS** restent non pris en charge. « Production » ne signifie pas support matériel universel. [Preuves et critères de publication](docs/validation/QA_LINUX_STABLE_SCOPE_2026-10-22.md).


**Dernier état de certification (21 octobre 2026).** Les essais Codespaces/GitHub ont couvert Rust, les sauvegardes Btrfs en VM, Snapper natif, l'annulation réelle via Qt, un banc CAS de 1 000 cycles, les paquets Debian 13/Fedora 44/Arch et les contrôles français/chinois. [Consulter la matrice de preuves et les limitations](docs/validation/QA_CODESPACES_RELEASE_CANDIDATE_2026-10-21.md). Les bilans R29/alpha9 ci-dessous sont conservés comme historique et ne remplacent pas le dernier contrôle du commit concerné. **Historique alpha9 : stable non publiée** : parité exhaustive des écrans Snapper, bureau Plasma complet et tests matériels de longue durée restent hors périmètre validé.

**Fork de Btrfs Assistant 2.3.2** intégrant les sauvegardes distantes Snapper, un moteur CAS Rust et une récupération UEFI avec ReaR.

[Guide utilisateur](docs/guides/UTILISATION_FR.md) · [Récupération de machine](docs/guides/RECUPERATION_REAR_FR.md) · [Tests et limites](docs/VALIDATION.md) · [Portes de release](docs/validation/RELEASE_GATES_CURRENT_2026-10-16.md) · [Cartographie](docs/PROJECT_MAP.md) · [Développement](docs/DEVELOPMENT.md) · [English](README.md)

> **0.1.0-alpha9 — préversion, pas version stable universelle.** La restauration complète a réussi sur des **disques virtuels QEMU**, pas sur tous les ordinateurs physiques. Conserver une sauvegarde indépendante et vérifiée. Btrfs Assistant officiel et Snapper ne sont pas remplacés.

## Fonctions

| Fonction | Disponible | Limite |
| --- | --- | --- |
| Btrfs et Snapper | Snapshots locaux, retour arrière, sous-volumes, maintenance, navigation | Snapper garde le contrôle des snapshots |
| Checkpoint v2 | Compatibilité Harbor historique, transferts interrompus, planification | Format distinct du CAS |
| Harbor CAS | Rust, FastCDC/BLAKE3, zstd, sauvegarde Btrfs complète/incrémentale, vérification de chaîne, staging | Snapshot source Btrfs en lecture seule et dépôt dédié |
| Rétention CAS | Plan de simulation, confirmation par empreinte, conservation des parents et blocs partagés | Suppression destructive interdite par défaut sur NFS/SMB |
| ReaR 2.9 | ISO UEFI, reconstruction GPT/Btrfs/ESP, restauration CAS et réparation automatique des deux chargeurs GRUB | Une racine Btrfs simple, ESP FAT32, UEFI x86-64, Secure Boot désactivé |

L'onglet **Sauvegardes distantes** rassemble les sources Snapper, la destination, les envois, l'inventaire, la vérification, la prévisualisation de récupération, la programmation et la rétention. Les archives des deux moteurs **ne sont pas interchangeables**.

## Compiler sans écraser le système

Prérequis : C++17, Qt6 Widgets/LinguistTools, CMake, Ninja, Rust/Cargo, libbtrfsutil, Python 3 et btrfs-progs. Snapper et polkit sont nécessaires aux opérations courantes.

    git clone https://github.com/GodsQuantum/BTRFS-Assistant-Harbor.git
    cd BTRFS-Assistant-Harbor
    cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
    cmake --build build --parallel 4
    QT_QPA_PLATFORM=offscreen ctest --test-dir build --output-on-failure
    DESTDIR="$PWD/staging" cmake --install build

Inspecter le résultat dans **staging/**. Installer ensuite uniquement un paquet compatible vérifié. Ne pas remplacer le paquet officiel Btrfs Assistant.

**Compatibilité des paquets — checkpoint du 16 octobre 2026 :** le DEB alpha9 révision 2 déjà publié sur GitHub **n'est pas compatible avec Debian 13 (Qt 6.8.2)**. Ne pas le forcer. Les nouveaux paquets R29 ont été compilés et testés dans de vraies VM UEFI/Btrfs : **Debian 13** `0.1.0~alpha9-9+deb13` (rev7→rev9→rev7→rev9→purge ; GUI X11 française à 125 %), **Fedora 44** `0.1.0-0.alpha9.10.fc44` (rev9→rev10→rev9→rev10→suppression), **Arch Linux** `0.1.0alpha9-9` (rev8→rev9→rev8→rev9→suppression), avec codes retour vérifiés. Voir les [journaux et SHA exacts R29](docs/validation/QA_ALPHA9_R29_GUI_CANCEL_PACKAGING_2026-10-16.md). Les trois paquets candidats **ne sont pas encore publiés en stable**. Ubuntu 26.04, l'environnement KDE Plasma/Wayland complet et le matériel utilisateur restent à qualifier ; un test Qt ciblé sous Weston headless a néanmoins réussi.

## Première sauvegarde, sans confusion

1. Créer ou sélectionner un **snapshot Snapper en lecture seule**.
2. Ouvrir **Sauvegardes distantes**, choisir la configuration Snapper et son snapshot.
3. Choisir checkpoint-v2 (ancien dépôt) **ou** CAS (nouveau dépôt dédié). Pour CAS, cliquer **Initialiser le dépôt CAS** dans un répertoire existant et vide.
4. Lancer **Envoyer l’instantané sélectionné**, puis **Afficher les sauvegardes** et **Vérifier l’archive**.
5. Pour tester la récupération, choisir un staging **Btrfs neuf et vide**, différent de la racine du système, et utiliser **Prévisualiser la restauration**.
6. Avant une suppression CAS, contrôler le plan de simulation et confirmer seulement le plan attendu ; ne pas forcer le GC destructif sur NFS/SMB.

### Dépôt CAS partagé entre plusieurs machines (candidat alpha9, non certifié stable)

Pour Pegasus et Galactica, sélectionner **le même dossier parent `Workstations/`**, jamais deux dépôts séparés. Le CAS crée `Workstations/.harbor-repo-id`, un seul `objects/`, puis `machines/<machine>/manifests/`. Le nom de machine vient du hostname et reste modifiable dans l'interface. Le moteur Btrfs fonctionne sur Linux avec des snapshots en lecture seule ; **Galactica/macOS ne dispose pas de Btrfs natif** et requiert un futur adaptateur APFS/fichiers et un format de restauration portable, non livrés dans cette alpha.

Une suppression d'archives d'une machine est soumise au **GC global** de tous les manifestes ; tous les chunks nécessaires aux autres machines restent conservés. Le GC destructif sur réseau NFS/SMB/SSHFS/9p reste bloqué faute de certification des verrous multiclients. Les anciens dépôts `manifests/` sont compatibles sans migration automatique. [Architecture CAS multimachine et limites QA](docs/CAS_MULTIMACHINE_2026-10-21.md).

Voir [le guide utilisateur détaillé](docs/guides/UTILISATION_FR.md).

## Récupération d'un système entier

**Preuve en VM Debian 13 / ReaR 2.9** : ISO créée depuis la machine source, nouveau disque 7 GiB GPT + ESP FAT32 + Btrfs, restauration externe de la racine via Harbor, reconstruction automatique des deux GRUB EFI, démarrage Debian **sans ISO** avec vérification du noyau, de l'ESP et des données.

Il ne s'agit pas d'un bouton de formatage dans la GUI. Le script de secours est **facultatif**, installé comme composant mais jamais activé automatiquement dans /etc/rear. Chaque machine réelle nécessite sa propre qualification : [guide ReaR](docs/guides/RECUPERATION_REAR_FR.md).

## État des tests et avertissements

Sur le commit `64cc7c2` : Rust all-targets, rustfmt et Clippy strict PASS ; **47 tests Python et 6 CTest/Qt PASS**, y compris navigation, français et annulation d'un groupe de processus. Essais X11/HiDPI, test Qt Wayland Weston headless, CAS/SMB3/NFS, Snapper et ReaR en VM. [Matrice détaillée](docs/VALIDATION.md).

**Snapper en VM :** 22 vérifications réelles (rétention, instantanés pre/post, différences et annulation des changements par undochange) ont réussi en Debian 13 UEFI/Btrfs. Les anciens bancs R30/R31 ont échoué (dépendance et synchronisation), mais trois nouveaux tests **R31b envoi, R32 réception, R33 GC local** ont interrompu brutalement le processus QEMU pendant les opérations, redémarré le disque et vérifié les restaurations, la non-réutilisation du staging partiel et le refus du plan de purge obsolète. Code retour du banc Python 0 pour les trois. [Résultats Snapper R32](docs/validation/QA_ALPHA9_R32_SNAPPER_RECEIVE_2026-10-16.md) et [coupures QEMU R33](docs/validation/QA_ALPHA9_R33_QEMU_POWERLOSS_EVIDENCE_2026-10-16.md).

**Non certifié :** parité ergonomique et fonctionnelle exhaustive de la GUI, annulation par bouton pendant un vrai transfert Btrfs, stress prolongé CPU/RAM/I/O, KDE Plasma Wayland et accessibilité. Les caches et contrôleurs physiques pendant une panne électrique ne sont pas reproduits par QEMU ; Secure Boot, LUKS/LVM/RAID, plusieurs racines système, GC destructif NFS/SMB et matériel physique demeurent non supportés sans démonstration réelle.

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
