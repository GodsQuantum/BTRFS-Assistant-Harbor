# Harbor — restauration d'un ordinateur en un clic (CachyOS)

## Contrat produit

Depuis un CachyOS fraîchement installé : Restaurer un ordinateur → Pegasus → date → ancien nom / nom de la nouvelle installation / nouveau nom → Restaurer.
L'utilisateur ne doit saisir aucune commande Btrfs, Snapper, LUKS ou Limine, ni assembler les volumes.

## État de la branche candidate

- La sauvegarde machine checkpoint-v2 sait inventorier les sous-volumes et le boot EFI, créer des snapshots Snapper frais ou natifs, archiver et vérifier des jeux datés.
- L'interface lance le processus de sauvegarde via systemd, indépendamment de la fenêtre privilégiée.
- Le catalogue mémorise le nom de machine d'origine.
- Le sélecteur graphique propose ordinateur, date, nom conservé ou changé, puis prévisualise et reçoit les volumes dans un staging Btrfs vide.
- Cette récupération ne touche pas la racine système active. Elle n'active PAS encore une restauration amorçable.

## Portes de certification bloquantes

1. Trouver le dépôt sur une nouvelle installation sans recopier de chemins ni entrer de commandes NFS.
2. Garantir la couverture de tous les sous-volumes persistants, la partition EFI et les archives vérifiées, même en cas de panne réseau.
3. Activer hors ligne les sous-volumes sur le nouveau disque tout en conservant sa configuration LUKS2, ses nouveaux UUID et les droits utilisateurs.
4. Restaurer ou reconstruire correctement les fichiers d'amorçage Limine, noyaux et initramfs, avec retour arrière garanti.
5. Appliquer réellement la politique de nom : origine, nom actuel, ou nom personnalisé ; gérer identifiants système et clés sans conflits.
6. Valider sur une VM UEFI représentative de Pegasus : GPT, ESP FAT32, LUKS2, Btrfs multi-sous-volumes et Limine, restauration d'un CachyOS neuf et boot sans ISO.
7. Apporter un parcours en un seul écran sans sélection manuelle de staging, ni commandes de dépannage ni choix de partitions.

## Configuration Pegasus vérifiée le 23 octobre 2026

- ESP vfat 4 Gio sur NVMe partition 1 montée sur /boot, chargeur Limine.
- NVMe partition 2 LUKS avec Btrfs et les sous-volumes /, /home, /root, /srv, /var/cache, /var/tmp, /var/log, et d'autres sous-volumes persistants.
- Audit actuel : 10 sous-volumes Btrfs inclus et un volume EFI indépendant.
- Le simple snapshot Snapper root 1768 transmis en CAS ne constitue pas une sauvegarde machine complète.
- Le backup en cours sur Pegasus ne doit jamais être interrompu pour les tests.

## Sécurité

Aucune restauration destructive, réinstallation, modification de disque ou reboot sur Pegasus. La PR reste draft et non installée en production tant que le boot LUKS2 + Limine n'est pas certifié en VM.


## Interface candidate à un seul bouton (23 octobre 2026)

- En ouvrant Sauvegardes distantes, deux grandes commandes s'affichent d'abord :
  Sauvegarder cet ordinateur et Restaurer un ordinateur.
- Les réglages Snapper, moteurs et commandes avancées restent sous Options avancées de sauvegarde.
- Si le dépôt habituel est accessible, Sauvegarder cet ordinateur lance
  une tâche systemd native set-backup sans demander de snapshot ni de partition.
  Si aucun dépôt n'est monté, une première sélection de dossier est nécessaire.
- set-backup verrouille le profil et reprend le seul jeu incomplet de cette
  machine et de ce dépôt, au lieu de repartir à zéro après une coupure.
  Les volumes avec Snapper utilisent des snapshots readonly frais; les autres
  des snapshots Harbor; la partition EFI est archivée séparément.
- L'observateur publie l'avancement machine (volumes, GiB, ETA) issu
  du journal systemd; il est consultable par l'UI et le systray.
- Restaurer un ordinateur demande machine, date et nom; Harbor prépare
  automatiquement un emplacement local Btrfs vide et root-only, sans chemin
  technique à saisir et sans toucher au système actif.
- Activation amorçable et application effective du nom: encore BLOQUÉES
  avant certification LUKS2 et Limine en VM UEFI; PR draft non déployée.


## Étape native : vérification CachyOS frais (23/10/2026)

Après réception des volumes et de l'EFI, l'interface lance automatiquement
checkpoint-v2 set-cachyos-plan en LECTURE SEULE. Le contrôleur compare la
racine reçue avec le CachyOS frais (Btrfs, ESP vfat à /boot, Limine,
fstab, UUID LUKS2 de la nouvelle installation, machine-id, noms et
sous-volumes). Il prépare les futurs noms de sous-volumes sans copier
le UUID LUKS, la phrase de passe ou le machine-id de l'ancienne machine.
Il rejette une sauvegarde incomplète, un mauvais hôte, une symlink hors
staging ou une nouvelle installation différente.

bootable_certified reste FALSE, activation_performed reste FALSE : aucun
changement du disque actif, de la configuration EFI, de la clé LUKS
ni du démarrage. L'activation hors ligne et le reboot validé en VM
CachyOS UEFI/LUKS2/Limine restent des critères BLOQUANTS.

## Identité du futur système (23 octobre 2026, candidat non activable)

- Le module autonome ne modifie que la nouvelle racine inactive Btrfs
  @harbor-ID-root : fstab, hostname, machine-id et crypttab issus du
  CachyOS neuf, ainsi que son /etc/default/limine adapté au futur rootflags.
  AUCUN ancien UUID LUKS de Pegasus n'est réutilisé.
- Pas de commande Limine, de modification EFI, de changement LUKS, de NVRAM,
  ni de modification ou renommage du systeme existant @ et @home.
- Test de bout en bout sur disque Btrfs jetable : deux sous-volumes, deux
  sauvegardes datees, restoration, creation de nouveaux volumes inactifs,
  comparaison des donnees et de la nouvelle identite.
- Il reste a activer Limine hors ligne et verifier un vrai demarrage CachyOS
  avec GPT/ESP, LUKS2, modules du noyau et retour arriere operationnel.

## Tentatives de restauration sans manipulation technique

En cas de coupure réseau ou de plantage durant la reception, un nouveau clic
Restaurer peut preparer automatiquement un nouvel emplacement vide :
/var/lib/btrfs-assistant-harbor/recovery/set-UUID/attempt-UUID. Les fichiers
incomplets anterieurs sont conserves pour examen et aucun dossier existant
n'est ecrase. Un garde de 16 tentatives pour le meme point empêche une
croissance illimitee sans avertissement. Le futur nettoyeur devra obtenir
une validation explicite avant d'effacer les receptions inachevees.
