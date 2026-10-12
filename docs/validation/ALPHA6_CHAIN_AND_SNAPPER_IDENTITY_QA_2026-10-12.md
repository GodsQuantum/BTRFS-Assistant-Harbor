# Btrfs Assistant Harbor — checkpoint QA après alpha6 (12 octobre 2026)

## Autorité et isolation
- Alpha6 source intacte : `/home/arezki/Dev/BTRFS-Assistant-Harbor-QA`, branche `qa/long-scheduled-backups-20261012`, HEAD `494242913114795c39530c8132051840e6e2b8a1`, tag `v0.1.0-alpha6`.
- Développement : `/home/arezki/Dev/BTRFS-Assistant-Harbor-QA-ChainFix`, branche isolée `qa/alpha6-chain-integrity-20261012` créée sur ce SHA exact.
- Host Cloud9 / CT700 / `arezki` UID 1000 seulement. Aucun accès Pegasus, aucune modification de montage, ACL, snapshots Snapper réels, sauvegardes ni services production.
- Toutes les 10 empreintes de la livraison **alpha6 initiale** `SHA256SUMS` étaient conformes. Ces installateurs ne contiennent **PAS** les corrections de ce worktree ; ne pas les déclarer à jour.

## Deux corrections fail-closed — tests reproduits RED puis GREEN

### 1. Chaîne incrémentale et `verify-stream`
- Défaut reproduit : `harbor-transport verify-stream` déclarait valide un incrémental après suppression de son manifeste parent, corruption de son objet parent, ou sans examiner le flux parent.
- Correction : validation complète des manifestes, UUID, empreintes et du chaînage parent→enfant, puis validation native `btrfs receive --dump -e` de chaque flux du parent initial à l'enfant. Aucune écriture de sous-volume dans cette commande.
- Test `transport/tests/chain_verify_tests.rs` : **3 RED/3** sur base alpha6, **3 GREEN/3** après correctif. L'archive synthétique sans provenance conserve son comportement autonome (ne peut pas prétendre à une chaîne incrémentale complète).
- Risque résiduel : vérification intégrale de chaque ancêtre coûteuse en I/O. Mesurer la latence sur chaînes longues / NAS avant optimisation sans baisse des contrôles ; aucune restauration réelle n'est prouvée par le seul `--dump`.

### 2. Noms Snapper recyclés dans le planificateur
- Défaut reproduit : une archive nommée `snap-CFG-N` pouvait être considérée sauvegardée quand un nouveau snapshot avec le même numéro N possédait un UUID différent. Un parent incrémental avec le même numéro mais un UUID différent pouvait aussi être proposé.
- Correction : `backend/cas_schedule.py` lit l'UUID de sous-volume Btrfs sur le snapshot readonly effectif et le compare à `source_uuid` issu de l'inventaire CAS avant un saut ou l'emploi d'un parent.
- Collision du snapshot courant : erreur bloquante, ancienne archive préservée, aucune fausse annonce de succès. Parent recyclé : nouvel envoi **complet**, pas d'incrémental invalide. UUID manquant ou illisible : refus de considérer la sauvegarde déjà faite.
- **3 nouveaux tests Python** : collision snapshot courant, parent invalide, lecture de UUID ; tous GREEN. Un nouveau schéma de nommage sans collisions est nécessaire pour reprendre automatiquement dans ce scénario, sans supprimer les archives existantes.

## Suites de certification exécutées sur code corrigé
| Test | Preuve | Résultat |
|---|---|---|
| Rust `cargo test --locked --all-targets` | `docs/validation/CHAIN_FIX_RUST_TESTS_2026-10-12.log` (journal local de DEV) | **37 pass**, 0 fail |
| Rust `cargo fmt --check` ; `cargo clippy --locked --all-targets -- -D warnings` | sortie terminale de DEV | PASS |
| Python `unittest discover -s tests -p test_*schedule.py` | `docs/validation/CHAIN_FIX_PYTHON_TESTS_2026-10-12.log` | **20 pass**, 0 fail |
| Python `compileall backend` et `git diff --check` | sortie terminale de DEV | PASS |
| Qt 6 CMake/Ninja build + CTest | `docs/validation/CHAIN_FIX_QT_CTEST_2026-10-12.log` | **2 pass**, 0 fail |
| QEMU Alpine 3.23.3 invité jetable, kernel Btrfs et binaire Rust MUSL corrigé | `docs/validation/CHAIN_FIX_QEMU_GUEST_BTRFS_2026-10-12.log` | **PASS** full + incremental, native receive, comparaison contenu/modes/hardlinks/symlinks/xattr/sparse ; corruption objet et parent absent refusés |
| Installateurs Arch, Ubuntu, Fedora | Empreintes de la livraison alpha6 originale uniquement | **10/10 SHA OK** — PAS reconstruits pour ce correctif |

Le test QEMU prépare un disque Btrfs **dans l'invité**, pas de montage sur hôte. `/tmp` invité et répertoire de test jetable sont effacés automatiquement à la sortie. Les cinq fichiers de traduction Qt modifiés par la génération `lupdate` ont été restaurés à la version initiale dans le worktree ; aucun changement de traduction n'est inclus dans le correctif.

## Documentation officielle et décision technique (12 octobre 2026)
- Btrfs `receive --dump` analyse/valide le flux mais ne fait pas de vraie restauration : https://btrfs.readthedocs.io/en/latest/btrfs-receive.html
- Btrfs snapshots non récursifs, vérification des UUID et des parents avant `send` : https://btrfs.readthedocs.io/en/latest/btrfs-send.html
- FastCDC 5.0.0 v2020 streaming conservé à version verrouillée : https://docs.rs/crate/fastcdc/5.0.0
- `btrfs-backup-ng` 0.9.5 conserve des verrous sur la destination pour bloquer le prune pendant les restores : https://github.com/berrym/btrfs-backup-ng. **Harbor CAS n'a pas encore cette garantie GC/prune multi-processus.** Ne pas activer de rétention destructive.
- Base amont Qt inchangée : Btrfs Assistant GitLab 2.3.2 (9 octobre 2026), SHA initial identifié dans les handoffs.

## Gates bloquants pour livraison comme sauvegarde principale
1. GUI KDE réelle / interaction Snapper et inventaire réel Pegasus, hors périmètre de cette session.
2. Capture machine complète : EFI/boot, /home, /var/log, autres sous-volumes Btrfs et partitions non-Btrfs ; restauration sur disque vierge avec double boot de validation.
3. CAS GC et politique de rétention avec graphe de parents, transactions crash-safe et **verrous de lecture/prune sur la destination**, sur toutes machines concurrentes.
4. Snapper : pin/lease de la source et du parent durant les longs transferts ; gestion automatique sans collision de noms après rotation et stress concurrent.
5. NFS de production : UID1000/ACL Dolphin, refus de fallback, veille réelle, timeouts et longues interruptions ; SMB3, SSH sécurisé, vérification d'identité de dépôt. Les tests isolés alpha5/alpha6 ne certifient pas Pegasus.
6. Journal/progrès/ETA persistants, endurance 300GiB–TiB et benchmark de coût de `verify-stream` sur chaînes incrémentales longues.
7. Une nouvelle reconstruction, installation et certification Arch/CachyOS + Ubuntu + Fedora du SHA corrigé, puis packaging SHA et signatures/attestations. Ancienne livraison alpha6 intacte.

**Décision :** ces correctifs sont aptes à être figés comme **checkpoint QA de développement isolé** ; **PAS** comme alpha7 production certifiée. Pas de mise en production, pas de sync du worktree vers le dépôt canonique avant levée des gates.
