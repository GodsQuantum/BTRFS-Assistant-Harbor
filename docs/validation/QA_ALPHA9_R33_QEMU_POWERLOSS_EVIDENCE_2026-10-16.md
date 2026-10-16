# R31b/R32 — Coupure réelle de QEMU pendant send et receive (16 octobre 2026)

**Statut : PASS dans le périmètre testé ; G15 reste PARTIAL pour GC sous coupure électrique.** Branche source QA `64cc7c2bf802901e5a677937aff71b1116991f3d`, binaire MUSL R26 SHA-256 `8b58055c5116693c90f4fad2255033aed1ce6cb54d34d5814afe30198259ed7d`. Ce sont des **invités QEMU Alpine 3.23.3 avec disque Btrfs virtuel**, pas des machines physiques. Pas de publication stable.

## Test R31b — Coupure pendant l'envoi
- Script `notes/qa-powerloss-qemu-r31b.py`, ISO et binaire validés par SHA en début de test. Crée 160 MiB de données aléatoires, snapshot RO et dépôt CAS local sur Btrfs.
- Attente d'au moins quatre objets CAS écrits alors que l'envoi reste actif et avant publication du manifeste ; écriture d'un marqueur de phase. `SIGKILL` envoyé **au processus QEMU**, pas seulement au CLI Harbor. Redémarrage à froid du même disque.
- Manifeste absent ou déjà vérifiable, ré-envoi si nécessaire, `verify-stream`, `receive`, comparaison intégrale `cmp`, propriété Btrfs RO puis shutdown ordonné.
- `notes/cert-alpha9-20261015/power-r31b-host.log` : quatre marqueurs PASS et `R31B_QEMU_POWERLOSS_FULL_PASS`. `power-r31b-host.time` : **Exit status 0**.

## Test R32 — Coupure pendant une réception
- Script `notes/qa-powerloss-qemu-r32-receive.py`, 160 MiB aléatoires et 60 fichiers témoins, dépôt CAS et snapshot vérifiés.
- Attente de fichiers effectivement créés dans le répertoire de staging **tant que la réception tourne encore** ; `SIGKILL` du processus QEMU et reboot à froid du disque virtuel.
- Contrôle que le staging partiel persiste mais qu'une réutilisation est refusée. Création d'un **nouveau staging vide**, reprise complète, `verify-stream`, `receive`, comparaison `cmp` des 61 fichiers, validation RO du snapshot.
- `notes/cert-alpha9-20261015/receive-r32-host.log` : `PASS INFLIGHT_POWERLOSS_TRIGGERED_DURING_RECEIVE`, `PASS GUEST_QEMU_ACTUAL_SIGKILL`, `PASS BTRFS_REBOOT_AFTER_POWERLOSS_RESTORE_VERIFY_CMP`, `R32_QEMU_POWERLOSS_FULL_PASS`. `receive-r32-host.time` : **Exit status 0**.

## Restrictions
- Le `SIGKILL` de QEMU reproduit une interruption brutale de l'exécution VM, **sans** simuler nécessairement la perte d'un cache disque physique volatile ou la corruption de blocs.
- Le GC local interrompu par `SIGKILL` d'un processus CLI est PASS R27 ; sa **coupure globale de VM pendant un GC actif** est toujours à reproduire.
- ReaR R8 certifié seulement pour un système UEFI x86_64 mono-racine Btrfs/ESP VFAT non-Secure-Boot ; LUKS/RAID/LVM, multi-racines, systemd-boot et GC destructif NFS/SMB toujours exclus.

## R33 — coupure réelle QEMU pendant GC (PASS)
- Script autonome notes/qa-powerloss-qemu-r33-gc.py créé hors Git ; en VM Alpine Btrfs deux archives retained et disposable, 160 MiB de données aléatoires. Un plan signé permet de supprimer disposable ; la phase où son manifeste est disparu alors que prune tourne encore est observée et confirmée par marqueur.
- Hôte : SIGKILL du PID QEMU (PASS GUEST_QEMU_ACTUAL_SIGKILL), puis cold reboot du disque virtuel. Ancien plan destructif REFUSÉ, sweep neuf de **23 objets orphelins / 122 848 160 octets**, retained vérifié et reçu dans un staging vide, contenu comparé et snapshot RO.
- notes/cert-alpha9-20261015/gc-r33-host.log : cinq marqueurs PASS, dont R33_GC_QEMU_POWERLOSS_FULL_PASS; gc-r33-host.time : **Exit status 0**, wall clock ~1m48. gc-r33-recover.log, gc-r33-stale.log, gc-r33-sweep.log, deux journaux consoles préservés et scratch QA effacé après succès. Le lanceur terminal a reporté un statut 1 malgré le message interne R33_GC_POWERLOSS_RC:0 ; le fichier /usr/bin/time confirme le code retour **0 du banc Python**. Aucun PASS n’est dérivé du seul statut du terminal.
- G15 est désormais PASS **dans ce périmètre QEMU** pour send, receive et GC coupés puis repris; il reste interdit de déclarer testés les disques physiques/caches hors VM ou de lever toute protection GC réseau.
