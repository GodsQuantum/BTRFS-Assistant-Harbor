# Btrfs Assistant Harbor 0.1.0-alpha7 — validation de préversion QA

## Provenance / périmètre
- Dérivé du tag alpha6 `v0.1.0-alpha6` (SHA `494242913114795c39530c8132051840e6e2b8a1`), via correctif QA `3d511d62c92476f50140ba4da753b3179d45f977`.
- Machine exclusivement Cloud9/CT700 utilisateur `arezki`, worktree isolé `/home/arezki/Dev/BTRFS-Assistant-Harbor-QA-ChainFix`.
- Les sources, paquets et montages de production ainsi que les snapshots Snapper et Pegasus ne sont pas modifiés par ces tests.

## Fonctionnalités développées sur la branche
1. `verify-stream` valide l'intégralité des parents CAS et les flux Btrfs (et pas seulement l'incrémental final).
2. Planification CAS : contrôle UUID source pour éviter les faux succès et les mauvais parents après réutilisation d'un numéro Snapper.
3. Sauvegarde CAS : mesures des octets bruts réellement parcourus, transmises sur stderr en trames `HARBOR_PROGRESS_BYTES=`; l'interface Qt affiche le total lu et le débit moyen depuis le début de la tentative, sans fausse ETA.
4. Restitution CAS : verrou **partagé** sur l'identité du dépôt durant toute la vérification et le native receive ; l'envoi garde son verrou exclusif. La concurrence locale est testée. Ce n'est PAS une preuve de compatibilité des verrous sur NFS ou SMB de production.
5. Compatibilité : aucun changement du format CAS v1, des noms des exécutables existants ni des archives checkpoint-v2.

## Preuves exécutées
- Rust : suite `cargo test --locked --all-targets` avec 39 succès au total (13 CAS, 3 chaîne, 7 CLI, 6 identité, 3 mountprobe, 7 retry), 0 échec. Journaux `READ_LEASE_RUST_TEST_2026-10-12.log`.
- Lints : `cargo fmt --check`, `cargo clippy -- -D warnings` réussis, `READ_LEASE_CLIPPY_2026-10-12.log`.
- Python : 20 tests `test_*schedule.py` réussis ; `ALPHA7_PYTHON_2026-10-12.log`.
- Qt 6 : compilation du fork Qt et de son transport Rust `/tmp/harbor-qt-progress-qa` réussie ; CTest 2/2, dont `--version` alpha7 ; `ALPHA7_QT_CTEST_2026-10-12.log`.
- VM QEMU Alpine indépendante : binaire MUSL post-intégration progression, vrai Btrfs full + incremental, byte-compare de la restauration, corruption/parent perdu refusés ; `PROGRESS_QEMU_E2E_2026-10-12.log`. **La fonction read_lease ajoutée ensuite a été testée par suite Rust, mais la VM doit être rejouée au SHA final.**
- Paquets Arch, Ubuntu, Fedora : **non encore recompilés au SHA alpha7** au moment de cette note. Ne pas présenter les vieux installateurs alpha6 comme alpha7.

## Périmètre non certifié — pas de remplacement de la sauvegarde principale
- Confrontation vraie GUI KDE sur Pegasus et lecture exhaustive de sa topologie Snapper, hors périmètre sans autorisation machine explicite.
- Restauration EFI/boot, partitions non-Btrfs, autres sous-volumes Btrfs, fstab/initramfs/bootloader et double démarrage de récupération sur disque vierge depuis ce fork Qt.
- Rétention destructive CAS avec analyse graphe parents/enfants et verrouillage distribué multi-machine lors du prune/restore. Aucun GC destructif proposé.
- Snapper pin/lease en cours de transfert et traitement automatique collision archive UUID/numéro.
- Véritables NFS/SMB de production avec ACL/droits Dolphin, test sleep long, hang NFS hard, et transfert volumétrique 300 Gio–1 Tio.
- Destinations SSH chiffrées, méthode de restauration fichiers individuels avec recherche, ETA production fiable et durabilité du suivi après fermeture totale de la GUI.
- Les tests sur conteneurs/VM ne remplacent pas l'essai de restauration sur la machine cible et une sauvegarde secondaire indépendante.

## Conditions de promotion
Conserver l'app officielle Btrfs Assistant disponible et les archives existantes. Proposer alpha7 uniquement en mode **préversion développeur / essais contrôlés** jusqu'à levée des points ci-dessus. L'absence de preuve est distincte d'un test réussi.
