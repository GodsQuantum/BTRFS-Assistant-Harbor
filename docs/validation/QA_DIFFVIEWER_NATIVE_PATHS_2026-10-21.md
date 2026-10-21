# Harbor QA — Snapper DiffViewer, découverte native et chemins non fiables

**Date : 21 octobre 2026. Branche QA uniquement.**

## Correction

Le visualiseur de différences Snapper invoquait auparavant un shell avec un joker `ls` construit depuis le chemin d'un fichier provenant d'un snapshot. Dans l'interface exécutée en root, un nom comportant des métacaractères pouvait être interprété par le shell au lieu de rester un chemin littéral.

La recherche passe désormais exclusivement par `QDir` et `QFileInfo` :

- Découverte des seuls dossiers de snapshots numérotés valides.
- Refus des chemins hors du snapshot sélectionné et des liens symboliques sortants.
- Aucun `bash -c`, `ls` ni interpolation de métacaractères.
- Sélections absentes du tableau gérées sans dereferencement de pointeur nul.
- Préservation du rendu des diffs et des dates Snapper des snapshots valides.

## Vérification

Nouveau cas dans `tests/test_gui_user_smoke.cpp` : crée trois snapshots valides et invalides sur un dossier temporaire, utilise le nom littéral `qa ; $(touch SHOULD_NOT_EXIST).txt`, vérifie que les deux vrais fichiers sont inventoriés, exclut la cible d'un symlink externe et les dossiers non numériques, et confirme qu'aucune commande externe n'est exécutée. Aucune sauvegarde réelle n'est utilisée.

**Tests locaux du correctif** : compilation Qt Release, CTest 6/6 et QTest sous le compositeur KDE KWin5 Wayland PASS dans le Codespace. La certification GitHub de la version EXACTE de ce correctif est nécessaire avant publication ; l'ancien candidat 6c3be79 a 11/11 jobs PASS mais ne contient pas encore cette correction.

**Périmètre** : cela certifie une recherche de fichiers non-shell dans le visualiseur. Cela ne remplace pas une certification complète de toutes les opérations de restauration sur un ordinateur réel, ni une analyse exhaustive de tous les autres modules upstream.
