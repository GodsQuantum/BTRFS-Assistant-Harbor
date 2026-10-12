# Btrfs Assistant Harbor alpha8 — validation de développement, 13 octobre 2026

Cette alpha8 est une **préversion expérimentale contrôlée** basée sur alpha7.
La production, les chemins de backup actifs, Pegasus et Btrfs Assistant officiel
n'ont pas été modifiés.

## Implémenté

- Sous-commandes `harbor-transport prune --repo ... [--name ...]`
  (simulation par défaut) et `--confirm-plan SHA256` (destructif explicite).
- Les archives retenues sont vérifiées et leur chaîne incrémentale
  UUID/parent est analysée avant toute suppression.
- Élimination sûre des références CAS: suppression des manifests sélectionnés
  avant nettoyage des seuls objets orphelins, avec synchronisation.
- Verrous exclusifs / partagés pour éviter la concurrence locale entre prune
  et lecture, envoi et restauration. Les accès aux fichiers utilisent O_NOFOLLOW.
- Boutons Qt de simulation/suppression d'une archive CAS et balayage des
  seuls orphelins avec boîte de confirmation; chemin et archives validés.
- Test QEMU Alpine invité natif Btrfs: contrôle parent, suppression incrémental,
  restauration du parent survivant, ainsi que parcours full/incremental.

## Validé dans CT700, environnement jetable

- 48 tests Rust: 13 CAS + 3 chain + 7 CLI + 9 GC + 6 identité
  + 3 sondes de montage + 7 retry; rustfmt et Clippy -D warnings.
- 20 tests Python des profils et planifications (11 CAS + 9 checkpoint).
- Compilation Qt6 Release et CTest 2/2; version `0.1.0-alpha8`.
- CLI `prune` sur repo temporaire: tokens rejetés si invalides,
  blocs partagés conservés et orphelins nettoyés.
- QEMU Btrfs natif: sauvegarde/full/incrémental et restauration avec
  CRC et métadonnées, échec sur parent/corruption, GC parent protégé.

## Ne pas assimiler au remplacement complet

Les points suivants exigent encore certification:
1. Concurrence **entre différents clients** et verrouillages NFS/SMB avec ACL
   et reconnect/disconnect sur partage réel (aucun montage existant modifié).
2. Restauration disque vierge multi-sous-volumes, partitions non-Btrfs,
   EFI/UEFI, chargeur d'amorçage, fstab et initramfs.
3. Validation UI KDE/Wayland d'un utilisateur sur machine explicitement
   autorisée; compatibilité fonctionnelle complète Btrfs Assistant.
4. Rétention automatique avec politique versionnée, protection des sources
   Snapper pendant sauvegarde, multi-terraoctets et résilience aux arrêts.
5. Signatures et publication de paquets certifiés; source snapshot versionné
   ne constitue pas une release stable.

Le prune reste **manuel et explicitement confirmé**. Aucun cron/timer
de suppression automatique n'est installé.
