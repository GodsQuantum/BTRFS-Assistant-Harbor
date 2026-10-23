# HANDOFF — Btrfs Assistant Harbor / restauration integrale CachyOS
Date de référence : 2026-10-23, environ 12:20 CEST (Europe/Paris)
Statut : CHANTIER EN COURS — NE PAS CONFONDRE CERTIFICATION DES COMPOSANTS ET RESTAURATION DEMARRABLE

## Objectif utilisateur (non negociable)

L'application publique Harbor doit fonctionner sur une diversité de machines et distributions compatibles, pas seulement sur Pegasus. Parcours demandé sur Pegasus / CachyOS :
1. Un seul bouton « Sauvegarder cet ordinateur » : sauvegarde COMPLETE (tous sous-volumes persistants Btrfs, /home, /srv, /root, fichiers EFI, systeme, applications, configurations et utilisateurs) vers un depot distant date, avec deduplication/reprise, barre de progression Gio et ETA dans UI et survol systray.
2. Un CachyOS FRESH installe sur un ordinateur neuf : « Restaurer un ordinateur » -> choisir « Pegasus » -> DATE -> soit garder le nom Pegasus, soit conserver le nom deja attribue a la nouvelle installation, soit donner un nouveau nom -> « Restaurer ».
3. Harbor doit gerer automatiquement depot distant, identite machine, Btrfs, LUKS2, fstab, EFI, initramfs, Limine, et BOOT REEL sans lignes de commande pour l'utilisateur. Retour arriere possible vers CachyOS frais en cas d'echec. Aucun faux message « restauration terminee » avant le demarrage confirme.
4. Une snapshot Snapper pre/post update de la racine N'EST PAS une sauvegarde integrale. La sauvegarde originale CAS Snapper #1768 sur Pegasus a reussi, mais elle est root-only; ne pas l'utiliser pour certifier le bare-metal.
5. UI multilingue francais, anglais, chinois simplifie. Native first; ne pas creer de wrappers custom inutiles. Pas de reboot automatique, ni de modification destructive sur Pegasus.

## Sources et points d'acces EXACTS

GitHub : https://github.com/GodsQuantum/BTRFS-Assistant-Harbor
PR CANDIDATE #5 (draft) : https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/pull/5
Branche de travail : feat/whole-computer-recovery-20261023
Dernier commit de CODE inclus dans la branche au moment du premier enregistrement du handoff : ccd2a29d5c6593815cd9e0a9cf14f0ddf47b400b (un commit de tests etait arrive entre le diagnostic d733a5b et le commit documentaire).
NE PAS SE FIER A UN SHA IMPRIME DANS UN ANCIEN CHAT : verifier git rev-parse HEAD et git status -sb.
Dev actif : Cloud9 LXC700 /home/arezki/Dev/BTRFS-Assistant-Harbor
Espace projet NVMe /home/arezki/Projets/HomeLab/BTRFS Harbor/
Miroir chemin hote Cloud9 /srv/storage/nvme/DEV/Projets/HomeLab/BTRFS Harbor/
Guide/contrat complet : docs/guides/RESTAURATION_COMPLETE_CACHYOS_FR.md
Handoff canonique de cette reprise : docs/handoffs/HANDOFF_HARBOR_CACHYOS_2026-10-23.md (copie dans l'espace NVMe projet).
Fichier historique HANDOFF_CURRENT.md : en-tete date du 16 octobre, chantier Alpha9 devenu OBSOLETE. Lire en priorite CE fichier 23 octobre.
Version Pegasus actuellement installee : Harbor 0.1.5 stable; NE PAS installer la branche PR #5 en production avant certification boot.
ACCEDER A CLOUD9 ET CT700 EXCLUSIVEMENT PAR SentinelX, PAS Remote Desktop Commander.
Exemple pour travailler sur CT700 : avec sentinel_exec host_id cloud9, executer « sudo -n /usr/sbin/pct exec 700 -- runuser -u arezki -- bash -lc 'COMMANDES' ».
Pour Pegasus : connexion via Cloud9 LXC400 MCPProxy profil ssh-actions:run-command / privileged-command, profile=pegasus. Eviter de changer ses montages, son chiffrement, ses partitions et son boot.

## Etat REEL au 23 octobre ~12h20

La branche Git ci-dessus etait CLEAN avant le commit de ce handoff.
Derniere CI integrale entierement VERTE sur code precedent : run 39929982272, SHA 9f67d41a24a0c82491b969040a17a40c388bec0e. Les jobs couvrent Rust, Qt/Python Ubuntu 24/26, vrai NFS, 1000 cycles CAS, Btrfs via QEMU, Debian 13, annulation GUI.
Sur SHA d733a5b :
- Workflow nouveau « CachyOS UEFI recovery lab » run 39937485158 : SUCCESS (ISO officiel CachyOS desktop 260809, hash SHA256 publie et inventaire ISO valides). Ceci N'EST PAS un boot.
- Certification generale run 39937489558 : EN COURS lors du dernier examen. Les jobs Native Snapper Btrfs, Rust, Qt Ubuntu 24/26 deja SUCCESS; autres jobs NFS, CAS soak, QEMU, Debian, Qt annulation encore in_progress. Verifier le resultat final sur GitHub avant de declarer tout vert.
- La CI peut etre relancee ou un run annule automatiquement lorsqu'un nouveau commit arrive; bien distinguer cancelled et failed.
GitHub Actions : https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/actions
Workflow ISO : .github/workflows/cachyos-uefi-recovery-lab.yml
Workflow complet : .github/workflows/certification.yml

Pegasus original root-only CAS : btrfs-assistant-harbor-job@e9ae1ccd-36e6-4cdd-81e5-9341eefbe020.service = INACTIVE, Result=success, ExecMainStatus=0 au dernier controle. Manifeste present sous depot Cloud9 backup-local/Workstations/machines/Pegasus/manifests. Il n'y a PAS encore de sauvegarde integrale machine-set de Pegasus en production. AUCUNE nouvelle sauvegarde complete sur Pegasus n'a ete declenchee pour cette branche.
Serveur Cloud9 depot de sauvegarde : /srv/backup-local/Workstations/ sur hote, monte sur Pegasus /mnt/Cloud9/backup-local/Workstations ; NFS pseudo export /backup-local. Ce chemin est la destination personnelle connue, mais le logiciel public ne doit PAS etre code en dur pour Cloud9. Le nouveau CachyOS doit decouvrir ou se faire associer le depot facilement.

## Fonctions developpees ET TESTEES (mais PAS certifiees bootables)

- Deux commandes principales Qt : « Sauvegarder cet ordinateur » / « Restaurer un ordinateur »; options avancees Snapper/CAS repliees.
- Native checkpoint-v2 set-backup sous systemd, sans garder GUI ouverte, verrouillage profil/destination, reprise des streams interrompus, nouvelle date pour nouvelle sauvegarde complete.
- Capture au debut de tous les snapshots Btrfs persistants + des fichiers /boot EFI; UUID/horodatages journalises; ancienne capture incomplete ou trop vieille preservee et abandonnee de maniere controlee.
- Catalogue machine/date/nom d'origine et choix original/nouveau/nom custom. Recuperation de volumes et EFI en staging Btrfs root-only; nouvelle tentative attempt-UUID pour chaque essai sans ecrasement.
- Estimation Gio/ETA et nombre de volumes dans UI + systray via status systemd securise.
- Preflight CachyOS lecture seule : sous-volumes et fstab, ESP FAT32 /boot, chiffrement LUKS2, UID machine, nouvelle racine et valeurs rootflags Limine. L'ancien LUKS UUID de Pegasus ne doit PAS contaminer le disque neuf.
- Construction de nouveaux sous-volumes Btrfs INACTIFS @harbor-ID-root, @harbor-ID-home etc. Ancien @ de CachyOS frais et ses autres volumes non touches.
- Materiel de configuration fstab, hostname, machine-id, crypttab et /etc/default/limine mis en place uniquement dans la NOUVELLE racine INACTIVE; pas dans le systeme actif.
- Plan de menu Limine ADDITIF et sa preparation sur ESP VFAT JETABLE; entree de boot existante conservee, pas de modification Pegasus. Refus si Secure Boot et autres configurations non certifiees.
- Tests Python/Qt multiples, QEMU Btrfs, Btrfs sur loopback, 2 dates/2 volumes/restore, LUKS2 Argon2id sur image jetable, preuve en-tete LUKS inchange, comparaison fichiers, vraie ESP FAT32 de test. Voir .github/workflows/certification.yml et tests/qa_cachyos_luks2_loopback.sh.
- Tests de l'ISO officiel realises : tests/qa_cachyos_iso_inventory.py et workflow ISO distinct; ISO non transfere vers Cloud9.

Fichiers essentiels :
- vendor/harbor-legacy/btrfs_backup_ng/core/cachyos_activation_plan.py
- vendor/harbor-legacy/btrfs_backup_ng/core/cachyos_activation_probe.py
- vendor/harbor-legacy/btrfs_backup_ng/core/cachyos_inactive_subvolumes.py
- vendor/harbor-legacy/btrfs_backup_ng/core/cachyos_inactive_config.py
- vendor/harbor-legacy/btrfs_backup_ng/core/cachyos_limine_recovery_entry.py
- vendor/harbor-legacy/btrfs_backup_ng/core/cachyos_offline_esp.py
- vendor/harbor-legacy/btrfs_backup_ng/cli/machine_set_v2.py
- src/ui/RemoteBackupWidget.cpp et src/util/RecoveryStaging.h
- tests/qa_oneclick_btrfs_loopback.sh, tests/qa_cachyos_luks2_loopback.sh
- tests/test_cachyos_*.py
- .github/workflows/cachyos-uefi-recovery-lab.yml

## Addendum indispensable — ajout de tests recu pendant le handoff

Commit de code ccd2a29d5c6593815cd9e0a9cf14f0ddf47b400b :
- test(machine): exercise production EFI and Btrfs full-machine archive in isolated mount namespace.
- Fichier nouveau : tests/qa_full_machine_efi_fixture.py.
- Fichiers modifies : tests/qa_cachyos_luks2_loopback.sh et docs/guides/RESTAURATION_COMPLETE_CACHYOS_FR.md.
- Attention : validation d'archives EFI+Btrfs sur runner isole =/= restauration demarrable CachyOS.
- A la reprise, ouvrir et executer ce nouveau test; verifier qu'il est bien inclus dans la CI et ne supprime aucune garde sur /boot ou mount namespace.
- CI en mouvement : apres push documentaire, workflow general courant le 23/10 vers 12:22 CEST = run 39938499291 (en cours a cette heure). Les anciens 39937489558 et 39938109317 ont ete annules par de nouveaux commits, ne pas les decrire comme des echecs de tests. Toujours consulter run plus recent pour HEAD.

## POINT PRECIS OU REPRENDRE — TOP PRIORITES

PRIORITE P0 — RESTAURATION VRAIMENT DEMARRABLE, PAS ENCORE REALISEE.
1. Controler dernier etat des 2 workflows SHA d733a5b, leurs logs et artefacts, corriger tout echec; si une autre session pousse du code avant reprise, fetch/rebase sans ecraser worktrees.
2. Exploiter le media officiel CachyOS 260809 deja SHA-valide dans un runner GitHub jetable : concevoir une installation FRESH REELLE dans QEMU/OVMF avec GPT, ESP VFAT /boot, LUKS2, Btrfs multi-sous-volumes, noyau/initramfs, Limine. Ne pas pretendre que l'inventaire ISO constitue cette installation.
3. Dans cette VM : restaurer un set machine-date multi-volumes complet (y compris EFI), maintenir l'OS fresh en fallback, activer un choix de racine recuperee, reconstruire initramfs / noyau compatibles et l'entree Limine native additive (limine-mkinitcpio si necessaire), preserver nouveau UUID LUKS, nom choisi, fstab/crypttab et machine-id cible.
4. DEMARRER LA VM DEPUIS DISQUE SANS ISO, verifier via console/login le hostname et un fichier temoin de / et de /home; redemarrer aussi sur le systeme fresh original (rollback). Tester variantes nom d'origine et nom nouveau.
5. Tester coupure/reprise/rejet fail-closed, ESP manquante, bootloader change, LUKS incorrect, kernel sans modules, Secure Boot non pris en charge, ressources/temps I/O.
6. Si P0 green : coupler l'activation CERTIFIEE au bouton Restaurer ordinateur. Jusque-la, laisser bootable_certified=false et PR DRAFT, ne pas publier en version finale.
PRIORITE P1 — APPLICATION ET UTILISABILITE.
7. Auto-detection/association simple de depot distant pour CachyOS NEUF, sans commandes NFS manuelles; mecanisme generique Linux (pas profil Cloud9 hardcode).
8. Confirmer GUI FR/EN/zh, deux boutons, sauvegarde sans questions techniques et progression Gio/ETA dans GUI/systray ; proof avec fermeture reelle.
9. Verifier que sauvegarde complete est reconstitutive sur un autre disque / nom different et qu'aucun service necessaire n'est oublie (/home, /root, /srv, sous-volumes persistants, EFI, configurations).
10. Terminer CI et certification exhaustive; seul ensuite promouvoir PR #5 vers main, creer release avec paquets, installer mise a jour Pegasus SANS DOUBLONS et programmer/realiser une sauvegarde complete vers backup-local/Workstations/Pegasus (attention conservation des archives et espace disque); ne pas interrompre aucun job actif et ne jamais redemarrer sans avertir l'utilisateur.
11. Git commit/push a chaque avancee, nettoyer seulement les artefacts temporaires de DEV que le processus possede, conserver historiques/archives/manifests/protections et mettre a jour le handoff final.

## Commandes de reprise recommandees (lecture seule d'abord)

Sur CT700 :
  cd /home/arezki/Dev/BTRFS-Assistant-Harbor
  git status -sb
  git fetch --all --prune
  git log -5 --oneline
  gh pr view 5 -R GodsQuantum/BTRFS-Assistant-Harbor --json isDraft,state,headRefOid,url
  gh run list -R GodsQuantum/BTRFS-Assistant-Harbor --limit 8
  sed -n '1,180p' .github/workflows/cachyos-uefi-recovery-lab.yml
  sed -n '1,160p' docs/guides/RESTAURATION_COMPLETE_CACHYOS_FR.md

Tests de base sur CT700 :
  PYTHONPATH=vendor/harbor-legacy:. python3 -m unittest discover -s tests -p 'test_*.py'
  python3 tests/qa_translation_coverage.py
  git diff --check
Consulter la configuration CMake du projet pour compiler Qt/Rust et lancer les CTest. N'EXECUTER les tests destructifs LUKS/Btrfs/ESP que sur runner/VM disposable avec garde GITHUB_ACTIONS et disques temporaires; jamais sur Pegasus ni sur le depot Cloud9.

## Règles de sécurité et d'honnetete

- Cloud9 : acces uniquement par SentinelX. Pegasus : via Cloud9 LXC400 MCPProxy ssh-actions. Ne pas basculer sur Remote Desktop Commander.
- NE PAS toucher aux disques /boot, LUKS, EFI, hostname, utilisateurs, montages NFS, systemd ni reboot de Pegasus pour un test.
- NE PAS annuler son job root-only CAS termine, ni effacer des objets CAS/manifests/archives.
- NE PAS promouvoir PR #5, taguer une release bare-metal ou annoncer « certifie complet » avant un VRAI boot CachyOS restaure sur disque virtuel, avec login et repli.
- Ne pas construire une app limitee aux seules integrations/montages de Pegasus : le parcours doit rester generaliste, adaptatif, native first.
- Rester focalise sur le resultat, travailler et corriger plutot que demander des confirmations de detail.
