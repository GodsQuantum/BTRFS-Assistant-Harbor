# Développement distant — Codespaces / GitHub Actions (21 octobre 2026)

## Source de vérité

Le dépôt [GodsQuantum/BTRFS-Assistant-Harbor](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor) est la source de code canonique du produit. La branche `cert/alpha9-20261015-qa-hardening` est une branche de qualification, **pas une version stable**. Protéger `main` avec PR, revue et contrôles CI avant fusion. Aucune release stable ne doit être construite à partir d'un commit non qualifié.

Codespaces fournit un environnement Ubuntu 24.04 avec Qt6, Rust, Python, btrfs-progs et compilation non privilégiée. Configuration : `.devcontainer/`. La base Ubuntu24 minimise la dérive ; GitHub Actions vérifie Ubuntu 24.04 et 26.04. Le Codespace ne contient **aucun dépôt CAS de sauvegarde utilisateur**, aucun jeton Cloud9 copié et aucun disque système de production monté.

## Workflow standard

1. Ouvrir un Codespace sur une branche de travail explicite.
2. `cargo fmt --check && cargo test --locked --all-targets && cargo clippy --locked --all-targets -- -D warnings` dans `transport/`.
3. Compiler la GUI avec CMake/Ninja, lancer CTest en `QT_QPA_PLATFORM=offscreen`.
4. Lancer les tests Python, puis la CI GitHub `.github/workflows/certification.yml`.
5. Examiner le statut de chaque job et les artefacts binaires, journaux et empreintes SHA ; corriger sur branche, pas sur `main`.
6. Publier un paquet **QA/candidat** seulement après compilation native. Une stable attend en plus les portes de certification matérielle / graphique ci-dessous.

### Suites et portabilité

| Porte | Exécution distante | Condition avant stable |
| --- | --- | --- |
| Rust sécurité, GC, FastCDC/BLAKE3, deux identités | GitHub Actions Ubuntu | Tous tests réussis, race TOCTOU inclus |
| Qt/CI, interface accessible au clavier, annulation CAS | GitHub Actions Ubuntu offscreen | QTest réel avec annulation pendant un stream et retry/verify |
| Deux vrais Btrfs send/receive | QEMU TCG sur runner GitHub | Journaux QEMU, comparaison contenu et xattrs/permissions |
| Deux clients Linux virtuels, même CAS | Deux invités QEMU séquentiels | 0 nouveaux chunks entre clients identiques, GC conserve 2e client |
| Debian 13 / Fedora 44 / Arch | Builders de distribution et paquets QA | Installation/upgrade/rollback/purge sur OS natifs |
| G09/G10 KDE Plasma Wayland et Snapper GUI | VM KDE dédiée (ou poste volontaire) | Preuves GUI/Wayland réelles, pas uniquement offscreen |
| G22 Annulation GUI d'un vrai Btrfs send | VM Btrfs/Qt dédiée | Processus enfants annulés, manifest non publié, retry + restore |
| G23 longue endurance/recovery | Environnement isolé adéquat | Seuils CPU/RAM/I/O/longévité et tests KVM physiques, hors TCG |
| Galactica macOS/APFS | Moteur futur distinct | **Non disponible** ; ne pas prétendre sauvegarde native macOS |
| GC destructif NAS NFS/SMB/9p | Aucun backend réseau certifié | Refus de suppression maintenu jusqu'à verrou distribué qualifié |

GitHub-hosted runners ne garantissent pas KVM/nested virtualization ; le test Btrfs utilise explicitement `accel=tcg`. Codespaces est un outil de *développement*, pas un remplacement magiquement équivalent aux tests systèmes Btrfs, UEFI, Plasma ou APFS.

## Politique de coût et sécurité

Choisir une machine Codespaces 4 vCPU / 16 Gio, région WestEurope si disponible, arrêt après 15 min d'inactivité, rétention de 7 jours. Les builds CI sur runners publics standards ont leurs règles de quota propres ; consulter les limites du compte. Ne pas exposer de ports applicatifs en public ni copier des secrets de Cloud9 dans le repo. Permissions CI `contents: read`, actions GitHub épinglées par commit SHA, rétention des artefacts QA limitée à 14 jours.

## Retrait progressif des artefacts Cloud9

Le workspace Cloud9 `/home/arezki/Projets/HomeLab/BTRFS Harbor` reste un point de secours tant que Codespace + tests CI n'ont pas passé et que les preuves QA n'ont pas été vérifiées sur GitHub. **N'effacer ni LXC700, ni `Projets/`, ni les chemins partagés** : ils appartiennent à plusieurs applications. Quand la migration est vérifiée, nettoyer uniquement les caches générables *identifiés* de Harbor (`build/`, Cargo `target/`, overlays QEMU jetables) en préservant rapports `notes/`, back-ups et vrais fichiers source ; noter les tailles avant/après. Aucune suppression de snapshots/volumes/montages ou backups PBS/SyncBridge.

## Bilan de reprise du 21 octobre (avant Codespaces)

- CAS multimachine : deux invités QEMU Linux indépendants, 3 chunks Pegasus, Galactica 3 réutilisés / 0 nouveaux, restauration SHA identique ; ce n'est pas un test APFS.
- G20 : accès Rust via descripteurs répertoire épinglés (`openat`/`linkat`/`unlinkat`), test concurrent d'interposition de liens symboliques PASS ; `cargo test` + Clippy strict PASS en DEV700.
- G22 : bouton Qt de véritable CAS FastCDC 384 Mio annulé, aucun manifest partiel, retry/verify PASS ; **annulation GUI de vrai Btrfs send non certifiée**.
- G23 : tests 600 archives en six séries, 137,48 secondes, pic RSS enfant 51 604 Kio ; endurance prolongée/KVM encore à qualifier.
- Btrfs : R49 QEMU TCG vrai envoi complet+incrémental et restauration PASS après changement openat.
- R48 Debian13/KVM GUI : **FAIL de préparation APT** (DNS externe + vieille entrée locale) avant le test, ne pas marquer G22 PASS.
- Stable **non certifiée** tant que portes ouvertes demeurent.

Tout résultat CI ultérieur prend préséance sur ces preuves locales **uniquement s'il s'applique au commit exact** ; conserver échecs et limitations.
