# ⚙️ Référence technique

[← Home](../README.fr.md) · [Setup and recovery](WORKSTATION_BACKUPS.fr.md)

**Fonctionnement.** Harbor conserve l'interface GPL Qt Btrfs/Snapper et ajoute le moteur Rust CAS ainsi qu'une compatibilité checkpoint-v2 distincte. Un seul dépôt \`Workstations/\` contient le marqueur \`.harbor-repo-id\`, les blocs communs \`objects/\` (FastCDC/BLAKE3+zstd) et les inventaires individuels \`machines/<nom>/manifests/\`. Les mêmes blocs sont réutilisés entre clients Linux compatibles.

**Répertoire NFS existant :** choisir la racine déjà montée ; ne pas créer \`Workstations/Workstations/\` ni de pools CAS séparés dans \`Pegasus/\` ou \`Galactica/\`. S'il manque les métadonnées CAS, les initialiser **dans la racine existante**, une fois, en préservant les dossiers présents. Contrôler positivement le serveur/export NFS : une perte du montage ne doit jamais provoquer une écriture dans un dossier local de substitution. \`harbor-transport init --repo /chemin/Workstations\` crée les métadonnées CAS nécessaires, pas un autre dépôt sur un autre volume.

**Sécurité :** les écritures et lectures NAS sont autorisées, mais le GC destructif CAS NFS/SMB/SSHFS/9p est refusé. En local, une suppression exige un aperçu puis une empreinte de plan correspondante. Restauration uniquement en zone Btrfs vide, jamais à la place de la racine active.

**Limites :** Linux x86-64 et snapshots Btrfs en lecture seule. Dans la CI, « Galactica » est un invité **Linux**, pas une sauvegarde Mac. Capture macOS/APFS, GC NAS distribué et récupération intégrale chiffrée/multiracines restent à développer et ne doivent pas être présentés comme acquis.

**Certification :** Linux 0.1.0 vérifié avec Rust, Qt/Python, Snapper/Btrfs loopback réels, deux invités QEMU Linux, annulation/reprise d'envoi, 1 000 cycles CAS et paquets Debian 13, Fedora 44, Arch. Voir le [périmètre](validation/QA_LINUX_STABLE_SCOPE_2026-10-22.md), [CAS multimachine](CAS_MULTIMACHINE_2026-10-21.md) et [preuves](VALIDATION.md).
