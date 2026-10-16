# Développement et futures mises à jour

Le dossier Git doit contenir **les sources, tests, packaging et documentation**, jamais les disques QEMU, dépôts de sauvegarde d'essai, caches ou secrets. Les artefacts restent hors Git. Les points d'entrée pour les prochaines sessions sont la [cartographie technique](PROJECT_MAP.md), les [portes de certification actuelles](validation/RELEASE_GATES_CURRENT_2026-10-16.md) et le `HANDOFF_CURRENT.md` du dossier canonique DEV700. Ne pas confondre les anciens worktrees v0.2.7-rc avec la branche alpha9.

## Convention de travail

- Sources Git sur **NVMe de DEV700**, dans un worktree de branche explicite.
- Build Qt et cargo target dans un dossier QA isolé **hors du dépôt**.
- VM ReaR/ISO et données CAS d'essai uniquement dans un laboratoire jetable clairement nommé.
- Handoffs, journaux de recherche et logs complets dans le dossier de projet canonique privé ; synthèses vérifiables dans docs/validation/.
- Ne jamais modifier montages NFS, fichiers ou snapshots Snapper existants, autres disques, permissions arezki et configuration Proxmox sans demande explicite.

## Commandes de validation

    cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
    cmake --build build --parallel 4
    QT_QPA_PLATFORM=offscreen ctest --test-dir build --output-on-failure
    PYTHONPATH=vendor/harbor-legacy python3 -m unittest discover -s tests -p 'test_*.py'
    cd transport
    cargo fmt --all --check
    cargo test --locked --all-targets
    cargo clippy --locked --all-targets -- -D warnings

Les changements de disque/UEFI exigent **un vrai démarrage d'un système restauré**, pas seulement un résultat positif de tests unitaires ou une génération d'ISO.

## Tests et publication

Les résultats du code actif R29 (et non ceux du tag alpha9 publié) sont regroupés dans [le rapport R29](validation/QA_ALPHA9_R29_GUI_CANCEL_PACKAGING_2026-10-16.md). Avant de nommer une version stable : reconstruire les trois paquets à partir du **dernier commit exact**, valider chaque paquet dans sa VM (installation → mise à niveau → retour arrière → désinstallation), vérifier les SHA-256 et le boot ReaR lorsque le code de récupération a changé, puis relire les portes de sécurité encore PARTIAL. La stabilité universelle ne peut pas être déduite du seul CTest Qt.

## Méthode de livraison

1. Lire le handoff courant puis vérifier git status, commit et cible de travail.
2. Documenter les recherches officielles actuelles et leurs implications.
3. Ajouter un test négatif puis un test positif pour chaque correctif.
4. Tester la GUI, les moteurs et la récupération en VM avant tout paquet.
5. Construire les paquets sur leur distribution cible ; documenter ceux non vérifiés.
6. Contrôler git diff --check, un arbre propre, les sources poussées et le SHA distant.
7. Mettre à jour README, guides, matrice, changelog et handoff.
8. Nettoyer uniquement ses caches et processus de tests identifiés, **jamais des données utilisateur**.

Ne pas annoncer « stable » pour Secure Boot, RAID/LUKS, GC destructif NAS ou autres fonctions non couvertes.
