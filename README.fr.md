# Btrfs Assistant Harbor — fork expérimental 0.1.0alpha6

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
