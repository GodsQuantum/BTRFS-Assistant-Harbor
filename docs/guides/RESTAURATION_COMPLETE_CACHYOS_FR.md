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

