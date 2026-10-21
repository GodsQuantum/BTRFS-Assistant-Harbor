# Alpha9 R44 / R45b — preuve CAS multimachine (21 octobre 2026)

**Statut : PASS dans le périmètre décrit ; version stable NON certifiée.**
Travaux uniquement sur Cloud9, dans CT700 sous UID 1000 `arezki`, par SentinelX.
Branche QA `cert/alpha9-20261015-qa-hardening`; HEAD de départ
`9ddd34fccaf75de3a40accfebc042c0b23994bf8`. Les sources candidates
contiennent des modifications de travail non commitées ; le vieux tag alpha9
ne représente PAS le code évalué ici.

## Source et identité de build

- Construction du nouveau moteur : `cargo build --locked --offline --release --target x86_64-unknown-linux-musl`, RC 0, sous LXC700/arezki.
- SHA-256 binaire Linux statique MUSL évalué :
  `6a55ed207ac8fe987cae1ce71a4dcc92b5cafc3cb42d53b31409216f0cc11afb`.
- Ancienne version statique utilisée dans R43 **non réutilisée**.
- `cargo test --locked --offline` : suites PASS dont 4 tests multimachines dédiés.
- `cargo fmt --check`, `cargo clippy --locked --offline --all-targets -- -D warnings` : RC 0 après correction de 3 lints des tests.
- `PYTHONPATH=vendor/harbor-legacy:. python3 -m unittest discover -s tests -p 'test_*.py'` : 50/50 PASS, RC 0.

## R44 — véritable Btrfs send/receive dans QEMU Alpine

- Exécution : `notes/vm-e2e-alpine-r43-tcg-performance.py` avec `--binary`
  pointant explicitement vers le nouveau binaire statique, ISO Alpine 3.23.3
  contrôlée SHA-256 et dossier de preuves propre à R44.
- Job SentinelX `job_da1408dba33b`, RC **0**, durée **126,7 s**.
- Invité Alpine Linux, noyau `6.18.7-0-virt`, environnement
  **QEMU TCG** (pas KVM, malgré la chaîne historique « KVM_3X » du runner).
- Marqueurs de réussite : `PASS FULL_INCREMENTAL`,
  `PASS KVM_3X_COLD_REPO_PERF`, `PASS E2E QEMU BTRFS ISOLATED`.
- Trois cycles sur dépôts Btrfs locaux fraîchement initialisés :
  envoi, vérification et restauration avec comparaison du contenu.
- Preuves brutes :
  `notes/cert-alpha9-20261015/R44_new_binary_full_incremental_soak/`
  (journal console, 3× JSON init/send/verify/receive).
- Première tentative R44 RC 1 avant démarrage de QEMU : Python du LXC700
  dépourvu de `pexpect`; correction par venv QA isolé, sans changer Python système.
- Il s'agit d'un banc fonctionnel et de trois cycles **en TCG**, pas d'une
  qualification d'endurance longue durée, KVM ou matérielle.

## R45b — deux clients Linux QEMU indépendants, même CAS

- Script de test versionné : `tests/qa_multimachine_two_qemu.py`.
- ISO Alpine 3.23.3 avec SHA-256 fixé ; QEMU **deux VM Linux distinctes**
  démarrées séquentiellement ; deux disques invités jetables.
- Un unique dossier `Workstations/`, marqueur
  `.harbor-repo-id`, verrou racine et un seul pool `objects/`.
- Chaque machine utilise uniquement son namespace de manifestes :
  `machines/Pegasus/manifests/` et
  `machines/Galactica/manifests/`.
- Statistiques avec le même payload de 12 MiB :
  Pegasus **3 nouveaux chunks**, Galactica **0 nouveau / 3 réutilisés**.
- Après changement du flux pour Pegasus : **2 chunks réutilisés**.
- Le GC destructif sur 9p est **refusé** comme attendu. La VM Galactica
  copie le dépôt dans son propre Btrfs temporaire puis supprime
  explicitement les archives Pegasus sous verrou local :
  **1 objet orphelin récupérable**, archive Galactica conservée.
- Restauration Galactica dans la seconde VM :
  SHA-256 source et sortie identiques :
  `4c6e63e347d893bf2a991be371f206f11fc85d3c31185aec1cab9073193c9efc`.
- Job SentinelX `job_c50da03fd19f`, RC **0**.
  Preuves : `notes/cert-alpha9-20261015/R45b_two_clients_Btrfs_local_gc/`
  (fichiers `pegasus-qemu.log`, `galactica-qemu.log`,
  `R45_results.json`).
- R45 initial avait FAIL à cause des permissions `root:root` du répertoire
  de restauration dans **la VM jetable** : correction du fixture avec
  `chown 1000:1000 /mnt/btrfs` avant restauration, aucune restriction
  de sécurité du produit supprimée.

## Compatibilité et limites

- Le format des archives historiques `manifests/` est conservé ;
  identifiant multimachine réservé `m@Machine@Archive`, impossible
  dans les noms legacy. Les tests Rust vérifient les anciens noms
  contenant `__`, les chaînes incrémentales indépendantes et le refus
  des liens parent entre machines.
- GC global : tous les manifestes machines et legacy sont examinés,
  et les chunks encore utilisés sont préservés.
- **Galactica désigne ici un client QA Linux**, pas le véritable Mac.
  Aucun adaptateur APFS/macOS ni restauration multiplateforme n'a été
  implémenté ou certifié.
- Pas d'accès aux véritables Pegasus/Galactica, aucun dépôt de
  sauvegarde utilisateur, aucun montage/ACL/snapshot/service de
  production modifié.
- NFS/SMB/SSHFS/9p : GC destructif toujours strictement interdit
  tant que les verrous multiclients ne sont pas qualifiés.
- Portes toujours ouvertes avant une publication stable : G09/G10
  (parité GUI et Plasma/Wayland/a11y), G20 (TOCTOU),
  G22 (annulation de transfert Btrfs réel par GUI),
  G23 (endurance CPU/RAM/IO et performance hors TCG), G26
  (packages candidats refaits et cycles de vie sur les cibles).

**Décision G26 : BLOCKED. Aucun tag ni package stable, aucune affirmation
de production-ready.**
