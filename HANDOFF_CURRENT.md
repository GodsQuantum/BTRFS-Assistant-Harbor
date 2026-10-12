# Btrfs Assistant Harbor — handoff actuel — 12 octobre 2026

## Sécurité et périmètre

Machine autorisée : Cloud9, LXC 700 uniquement. Ne pas lancer de commande
sur Pegasus, ne pas changer les montages Proxmox/NFS/SMB ni les ACL, ne pas
interrompre les sauvegardes de l'utilisateur. Le dossier CANONIQUE
/srv/storage/cloud/arezki/Projets/HomeLab/BTRFS Harbor/ ne doit PAS être
touché pendant le développement. Il sera utilisé uniquement après validation
explicite de la version destinée à la production.

## Développement

- Fork local : /home/arezki/Dev/BTRFS-Assistant-Harbor
- Branche : dev/remote-backups-harbor-20261012, issue de Btrfs Assistant 2.3.2.
- Worktree source sain ; développement enregistré dans cette branche uniquement.
- Ancien Harbor intact : /home/arezki/Dev/BTRFS-Harbor-v026, code
  historique de backup checkpoint-v2, version rc.6, SHA antérieur 24000f5.
- Build Qt + Rust CMake : /home/arezki/Dev/build-btrfs-assistant-harbor.
- Installation de STAGING seulement :
  /home/arezki/Dev/stage-btrfs-assistant-harbor.
- Aucun package installé sur Pegasus ni Cloud9 système, aucun push partagé,
  aucune branche upstream modifiée.

## Réalisations

1. Fork Qt avec application, launcher, desktop ID, icône et politique Polkit
   spécifiques, préservant les fonctionnalités historiques de Btrfs Assistant.
2. Onglet Remote backups : Snapper choisit le snapshot ; Harbor checkpoint-v2
   historique est toujours disponible pour envoi, inventaire, reprise et
   restauration stage, et un moteur Rust CAS FastCDC est sélectionnable pour
   dépôts dédiés, envois complets/incrémentaux, vérification et réception Btrfs.
3. Planification systemd pour le moteur historique : toutes les heures,
   quotidien, hebdomadaire. Installation sur machine de production NON réalisée.
4. CAS Rust : BLAKE3 pour blocs bruts, SHA256 des fichiers compressés et
   du flux complet, zstd niveau 1, déduplication valable même si le niveau
   zstd de l'objet déjà stocké est différent, fail-closed corruption, identités
   des snapshots et parents, limites de lecture, contrôles de montages et
   retries bornés pour erreurs réseau transitoires.
5. Répertoire distant écrit sous FSUID/FSGID du UID Polkit authentifié
   quand l'interface administrateur fournit PKEXEC_UID. Linux root peut
   ainsi lancer btrfs send/receive tout en produisant des fichiers CAS
   appartenant à UID1000 sur l'export. Contrôlé dans LXC700 et VM QEMU.
6. Tests natifs Btrfs en Alpine QEMU avec disque virtuel jetable : send et
   receive complet + incrémental, comparaison de fichiers, UUID Received,
   sous-volumes non récursifs, vérification des streams natifs, refus de
   restauration en cas d'objet corrompu et de parent absent, contrôle UID1000.
   Script réexécutable : transport/tests/vm/e2e_alpine_btrfs.py.
7. Compilation CMake avec Cargo.lock et staging incluant binaires GUI,
   Rust CLI et lanceur Python de programmation.

## Certification et tâches bloquantes

Ne PAS déclarer final production. Les tests locaux/VM ne prouvent pas la
résilience NFS/SMB face à de vraies coupures, un remontage d'export différent,
la veille d'une machine distante, ni la restauration bare-metal/EFI complète.
Les jobs systemd du vieux backend Python restent à auditer pour les droits
UID/GID/ACL. Le moteur CAS n'a pas de garbage collection/rétention, de
synchronisation SSH chiffrée, de planification récurrente autonome ou de
restauration fichier par fichier depuis Qt. Il faut également valider les
workflows GUI en session KDE réelle et empaqueter/signaler un paquet
d'installation Arch/DEB/AppImage/RPM destiné à la validation sur une machine
de test distincte.

## Protocole de reprise

Relire README.fr.md, docs/architecture/REMOTE-BACKUP-DESIGN-2026-10-12.md,
docs/architecture/QA-STATUS-2026-10-12.md et cette page. Continuer dans
cette seule branche LXC700, écrire tests d'abord, utiliser les derniers
btrfs-progs et FastCDC officiels. Ne pas déposer dans le dossier canonique,
ne pas installer sur Pegasus, ne pas nettoyer les données utilisateur.
