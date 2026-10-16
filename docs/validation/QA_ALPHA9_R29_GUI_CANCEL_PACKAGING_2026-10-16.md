# Harbor alpha9 R29 — annulation Qt, français, paquets réels (16 octobre 2026)

**Statut : candidat de certification, PAS DE STABLE / PAS ENCORE PRODUCTION READY.**

Workspace exclusif : LXC 700 DEV NVMe, `/home/arezki/Projets/HomeLab/BTRFS Harbor/`. Le miroir SyncBridge HDD, montages, ACL, snapshots et services Cloud9 n'ont pas été modifiés.

## Correctif Qt : annulation d'une opération

- Bouton **« Annuler l'opération en cours »**, inactif sans tâche et désactivé lors de son activation.
- Chaque CLI lancée par `QProcess` ouvre une session Unix isolée via `CreateNewSession` (support Qt depuis 6.7) ; SIGTERM au groupe, SIGKILL différé après 3 secondes seulement si le même QProcess est encore actif. Le test Qt lance un shell contenant un processus fils `sleep`, clique sur le bouton et vérifie la fin du processus **et** du groupe. Affichage français explicite de l'état d'annulation, sans transformer un abort en succès.
- Compilation Qt R29 : CMake RC0, build RC0, CTest 6/6 RC0 dans `notes/cert-alpha9-20261015/qt-r29-{rc.txt,ctest.log}`.
- Weston 10 / Debian 13 Qt 6.8 : compositing Wayland headless fonctionnel, `QT_QPA_PLATFORM=wayland`, **CTest GUI ciblé 1/1 PASS** ; `wayland-r29-candidate.log` et `wayland-r29-weston.log`. **Pas** une validation de session KDE Plasma Wayland complète ni une preuve de capture visuelle.
- `lupdate` réanalyse 404 entrées source (403 couples contexte/source uniques), catalogue FR 405 entrées, 0 entrée active manquante (`r29-i18n-coverage.log`). Captures et vrais X11/HiDPI R9 Debian13 conservés.
- Limite : le bouton est certifié en QTest avec processus descendant isolé, tandis que SIGKILL du **transport CAS réel** en plein envoi puis restauration a été démontré séparément en QEMU R22. Le clic du bouton pendant un vrai `btrfs send/receive` en environnement graphique n'a PAS encore été démontré. Aucun support annoncé pour annulation sûre d'un GC réseau destructif, toujours refusé par le CLI.

## Paquets du code GUI R29

| Plateforme | Identifiant | Preuve constatée | SHA-256 |
| --- | --- | --- | --- |
| Debian 13 / Qt 6.8.2 | `0.1.0~alpha9-9+deb13` | Compilation native + Qt CTest6/6 ; vraie VM UEFI/Btrfs, upgrade rev7→rev9→rev7→rev9, GUI française sous X11/125 % et purge. 30 commandes + QEMU RC0 : `vm-debian13-current-r9-lifecycle/qa-results.log`. | `3a191c555e209c881f510aec29846e6c7f480834f2ac1087c7bf82ea3c2323ca` |
| Fedora 44 / Qt 6.11 | `0.1.0-0.alpha9.10.fc44` | `rpmbuild` R29 CTest/Rust PASS. Correctif réel d'empaquetage : ne revendiquer que l'icône SVG plutôt que le répertoire partagé hicolor ; `%license .../*` recense MIT+GPL. VM Fedora 44 UEFI/Btrfs, install rev9→rev10→rev9→rev10→remove, 10 commandes + QEMU RC0 : `fedora44-r10b-boot-vm/qa-results.log`. Premier run r10 FAIL à cause d'une erreur de chemin d'un *script QA* vers le RPM rev9, conservé. | `68de6e98eda15807d5496876b16f370c5d95a0aa88a237915297fab775552c05` |
| Arch Linux 2026-10-15 / Qt 6.12 | `0.1.0alpha9-9` | Construction source R29 avec `makepkg` et tests Rust/Qt/Python PASS. Véritable VM Arch UEFI/Btrfs : pacman rev8→rev9→rev8→rev9→remove, tous codes 0, helper présent puis absent, QEMU RC0. Preuves `arch-r9-builder.log`, `arch-r9-boot-vm/qa-arch-r9-serial.log`. | `2d241727bf5c3d7ac49009e07a069842579d81c4724b7a7ae1df14b0fe06a553` |

### Limites de diffusion

Le tag `v0.1.0-alpha9` (commit `84159a0174c5785c41927d440c81f075f86d21a2`) demeure une préversion historique ; ses paquets ne correspondent pas au code R29. **Ne pas réutiliser les anciens paquets alpha9 comme preuve de la version stable.**

Non supportés et explicitement refusés par défaut : Secure Boot, LUKS/RAID/LVM, topologies de restauration système multi-racines, systemd-boot, GC CAS destructif via NFS/SMB. Non démontrés à ce jour : comportement sur matériel réel, coupure de courant VM pendant receive/GC, GUI KDE Plasma Wayland complète, parité GUI exhaustive Snapper/upstream, charge longue CPU/RAM/IO. Ne pas remplacer Btrfs Assistant existant sur Pegasus/Galactica/Cloud9 sans autorisation.

## Références upstream techniques
- [Qt QProcess::CreateNewSession](https://doc.qt.io/qt-6/qprocess.html) (since Qt 6.7 ; `setsid(2)`).
- [RPM spec %files / %license](https://rpm-software-management.github.io/rpm/manual/dynamic_specs.html) (déclaration explicite de fichiers/licences).
- [Btrfs Assistant upstream](https://gitlab.com/btrfs-assistant/btrfs-assistant) (inventaire réel des fonctionnalités à comparer).
