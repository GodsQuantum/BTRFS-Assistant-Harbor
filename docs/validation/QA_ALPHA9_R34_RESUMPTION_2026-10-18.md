# QA R34 — 18 octobre 2026

**Statut : certification incomplète. Aucune stable publiée.**

Périmètre : Cloud9 CT700 DEV, espace de travail NVMe. Git QA HEAD et distant : `a18444b02748506067a67e36438c5f9d4bcfff3c`. Tag alpha9 inchangé : `84159a0174c5785c41927d440c81f075f86d21a2`. Disque de travail : 314G disponibles (29 % utilisés).

## Contrôles réels

- Rust : `cargo test --locked --all-targets` RC0 (53 tests), `cargo fmt` RC0, `cargo clippy -D warnings` RC0.
- Python : 47/47 tests RC0 ; Qt CTest offscreen : 6/6 RC0.
- `cargo build --release --locked` RC0 ; SHA256 du binaire : `16f4013018277e53d85c3af475fc805e97a95bcd0928677a916feea1d39346f6`.
- Trois paquets candidats R29 : SHA256 3/3 OK. Preuves R33 : SHA256 13/13 OK, en exécutant la vérification depuis `notes/` pour résoudre correctement les chemins relatifs.
- Journaux R34 et manifeste SHA : `notes/cert-alpha9-20261015/R34_*_20261018.log` et `R34_SHA256_MANIFEST_20261018.txt` (8/8 OK).

## Portes encore ouvertes

G10 parité GUI Snapper, G20 tests de sécurité des chemins et des courses, G22 annulation GUI d'un transfert Btrfs réel, G23 CPU/RAM/I/O et endurance, G09 KDE Plasma Wayland complet. Ubuntu 26.04 et matériel réel non qualifiés. G15 reste PASS dans le périmètre QEMU R31b/R32/R33, sans extrapolation au matériel physique.

Un banc G23 a été préparé sous `notes/qa-g23-engine-soak-r34.sh` et validé en syntaxe Bash, mais son lancement n'a pas été autorisé par le terminal distant : **aucune mesure G23 nouvelle**. Aucun changement source ni paquet, aucun push stable. Aucun montage, ACL, SyncBridge, snapshot, sauvegarde ou service de production modifié.

## Références revues

- Upstream Btrfs Assistant : https://gitlab.com/btrfs-assistant/btrfs-assistant
- Qt QProcess : https://doc.qt.io/qt-6/qprocess.html
- Linux openat2 : https://man7.org/linux/man-pages/man2/openat2.2.html

Prochaine certification : scénarios G20/G22/G23 et vraie GUI Snapper/KDE en VM isolée, puis paquets reconstruits du commit final.
