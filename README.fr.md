# Btrfs Assistant Harbor — préversion expérimentale 0.1.0alpha9

Le fork conserve Btrfs Assistant 2.3.2 et Snapper comme gestionnaires de snapshots et des restaurations locales. Il ajoute un onglet de sauvegardes distantes avec deux moteurs indépendants.

- Checkpoint-v2 (compatibilité) : dépend du CLI Python Harbor btrfs-backup-ng installé séparément. Envoi manuel, inventaire, vérification, reprise des transferts inachevés et programmation systemd. Format historique .btrfs.zst conservé.
- CAS / FastCDC (expérimental) : CLI Rust harbor-transport construit et livré avec le fork. Initialisation du dépôt, sauvegarde Btrfs complète ou incrémentale avec parent explicitement identifié, blocs dédupliqués BLAKE3, compression zstd niveau 1, vérification SHA-256 et native Btrfs, restauration vers un staging Btrfs vide.

Le moteur CAS ne remplace PAS encore la récupération automatique d'un système entier, ni la sauvegarde EFI/boot de l'ancien Harbor. Aucun snapshot local n'est créé par le nouveau moteur ; Snapper en reste responsable. Les archives des deux moteurs ne sont pas interchangeables.

## Compiler dans un espace isolé

Prérequis : Linux, cmake, ninja, Qt6 Widgets et LinguistTools, libbtrfsutil, Rust/Cargo, Python3, btrfs-progs.

    cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
    cmake --build build -j 4
    ctest --test-dir build --output-on-failure
    cargo test --locked --manifest-path transport/Cargo.toml
    cmake --install build --prefix /chemin/prive/de/staging

Le test réel automatisé transport/tests/vm/e2e_alpine_btrfs.py utilise une VM Alpine et un disque Btrfs jetable. Il vérifie send/receive complets et incrémentaux, snapshots parents, SHA, contenu des fichiers, interruptions négatives et UID1000 avec PKEXEC_UID. Consulter docs/architecture/QA-STATUS-2026-10-12.md.

## Conditions indispensables avant la production

- SMB3 : coupure puis reprise en cours de transfert validées en laboratoire. NFSv4 : toujours non certifié sur un serveur persistant ; ne jamais changer les montages existants.
- Tester le contrôle utilisateur complet UID/GID et ACL sur chaque export, y compris les tâches planifiées par le moteur Python historique.
- Vérifier une restauration complète machine avec sous-volumes indépendants et EFI ; implémenter la rétention et le nettoyage des blocs CAS sans supprimer des parents utilisés.
- Valider sécurité SSH, restauration fichier par fichier, benchmark réaliste et paquets Arch/DEB/RPM/AppImage.

Ne pas écraser l'installation Btrfs Assistant d'origine, arrêter une sauvegarde en cours, ni substituer ce prototype à une sauvegarde de production.


## Tests réseau Linux de la version alpha5

Le laboratoire a validé sur des systèmes de fichiers réels : SMB3 avec
Samba, NFSv3 avec un serveur UNFS3 à stockage persistant, et NFSv4.1
avec un serveur NFS du noyau Linux dans une seconde VM Alpine.
Chaque scénario vérifie un envoi Btrfs complet et incrémental, un arrêt
temporaire du serveur après plusieurs blocs réellement écrits, sa
reprise, le flux natif et les fichiers reçus, et le refus d'écrire dans
le dossier local lorsque le montage réseau a disparu.

Planification CAS : Snapper reste propriétaire de ses snapshots. Le
timer systemd parcourt les snapshots existants, envoie le dernier en
lecture seule, vérifie l'archive parent avant tout envoi incrémental et
vérifie de nouveau une sauvegarde déjà présente. Deux moteurs disposent
de timers distincts, avec planification horaire, quotidienne ou
hebdomadaire, affichage et désactivation depuis l'onglet distant.

Important : ces tests ne changent pas les montages réels de Pegasus et
ne prouvent pas une restauration intégrale EFI/boot ni les performances
sur les sauvegardes personnelles de plusieurs centaines de GiB.
Le mode CAS est toujours un format distinct du Harbor checkpoint-v2
historique. N'utilisez pas l'alpha5 comme unique sauvegarde.


## Correctifs de certification alpha6

Les tâches systemd ne sont plus limitées arbitrairement à deux heures,
et le contrôle cryptographique d'un grand flux CAS n'est plus tué au bout
de 180 secondes. Le gestionnaire systemd peut interrompre un job au besoin
et les verrous/délais de reconnexion du moteur restent applicables.
Deux nouveaux tests reproduisent ces limites sur alpha5 puis confirment
leur disparition. L'interface indique le même numéro alpha6 que le paquet.


## Préversion alpha7 — essais contrôlés, pas une garantie de restauration universelle

- Chaînes incrémentales CAS vérifiées intégralement (parents et flux natifs).
- Les numéros Snapper recyclés sont contrôlés par UUID.
- Pendant les longues sauvegardes CAS, l'interface affiche les octets **bruts lus** et un débit moyen observé, et non un faux pourcentage ni une ETA.
- Les restaurations CAS conservent un verrou partagé du dépôt jusqu'à leur fin. Ce mécanisme est testé localement, pas certifié sur les NFS/SMB de production.
- Le GC/rétention destructrice CAS, l'inventaire machine complet EFI/boot, la restauration bare-metal, les connexions SSH et les ACL NFS de production restent hors couverture de cette préversion.
- Btrfs Assistant officiel et ses configurations Snapper existantes sont préservés et restent installables en parallèle.


### Rétention CAS contrôlée (alpha8, laboratoire)

L'onglet de sauvegarde distante permet désormais la suppression explicitement
confirmée d'une archive CAS et le nettoyage séparé des blocs inutilisés.
Le moteur `harbor-transport prune --repo CHEMIN [--name ARCHIVE]` émet d'abord
un **plan de simulation**, incluant le nombre de blocs orphelins et les octets
compressés récupérables. **Aucun fichier n'est supprimé par défaut.** L'action
réelle requiert la valeur `--confirm-plan SHA256` issue de cette simulation.
Le moteur recalcule et compare le plan sous verrou exclusif avant suppression.

Un parent exigé par un incrémental conservé ne peut pas être supprimé. Les
objets partagés restent tant qu'au moins une sauvegarde les référence. Toute
archive restante est vérifiée avant prune. Des anomalies de dépendances,
de métadonnées, de liens symboliques ou de montages entraînent le refus.

**Limites non certifiées :** verrouillage distribué NFS/SMB et reprise après
coupure réelle, restauration multi-sous-volume et EFI, très gros volumes,
environnement KDE Wayland réel. Ne pas activer de politique automatique de
suppression sur le NAS avant qualification indépendante. L'outil original
Btrfs Assistant et les sauvegardes existantes restent inchangés.


## Alpha9 — restauration réelle QEMU certifiée, ReaR encore bloquant

En octobre 2026, test isolé complet **PASS** : installation d'une VM
GPT + partition EFI FAT32 + racine Btrfs, sauvegarde de la racine avec
Harbor CAS et de l'ESP séparément, réception intégrale sur un second
disque virtuel VIERGE, nouvelle partition EFI, nouveau système Btrfs,
recréation du sous-volume racine, correction UUID et GRUB, puis vrai
redémarrage OVMF sans ISO et comparaison des fichiers restaurés.
Résultat : R5 exit 0; voir
docs/validation/QA_ALPHA9_UEFI_DISASTER_RECOVERY_R5_20261013.md.

Après R5 : 50 tests Rust, 33 Python, 3 Qt et Clippy sans avertissement,
plus test NFSv4 à deux clients à identifiants uniques.
Le nettoyage CAS destructif reste strictement refusé sur NFS/SMB.

**Important :** la restauration du disque a été *scriptée par la QA*,
pas par ReaR. L'ISO ReaR ne contient pas encore tous les composants
Harbor nécessaires, et son parcours EXTERNAL_RESTORE n'a PAS été prouvé
en VM. Ce fork reste une préversion; ne pas s'en servir comme seule
sauvegarde ni certifier la récupération automatique d'un PC.
Btrfs Assistant original et tous les snapshots/partages de l'utilisateur
restent intacts.
