# Développement et futures mises à jour

Le dossier Git doit contenir **les sources, tests, packaging et documentation**, jamais les disques QEMU, dépôts de sauvegarde d'essai, caches ou secrets. Les artefacts restent hors Git.

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
