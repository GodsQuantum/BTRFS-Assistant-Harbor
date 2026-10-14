# Secours UEFI / Btrfs avec ReaR et Harbor

**Attention : procédure avancée et destructive pour le disque choisi dans ReaR. À tester uniquement sur disque virtuel avant toute utilisation réelle.**

## Cas effectivement testé

Sous QEMU, Debian 13 avec **une racine Btrfs**, **une ESP FAT32**, **GPT**, **GRUB x86-64** et **Secure Boot désactivé** a été sauvegardé avec Harbor CAS et une archive séparée de l'EFI, puis restauré par **ReaR 2.9** sur un second disque vierge. ReaR a recréé partitions et systèmes de fichiers, invoqué son **EXTERNAL_RESTORE**, puis le script Harbor a restauré racine+ESP et réinstallé GRUB standard et de secours. Le système restauré a redémarré sans ISO avec un code de validation final nul.

## Composants

- **harbor-rear-restore** : script livré sous /usr/lib/btrfs-harbor/recovery/. Il ne partitionne aucun disque, cette responsabilité appartient à ReaR.
- **local.conf exemple** sous /usr/share/btrfs-harbor/rear/ : configure ReaR OUTPUT=ISO et BACKUP=EXTERNAL. **Pas de modification automatique de /etc/rear/local.conf.**
- **rear-rescue.example.conf** : profil avec dépôt CAS, nom de l'archive, sous-volume source et archive EFI SHA-256. Un administrateur doit adapter les chemins et conserver un fichier de profil root-owned.
- **harbor-transport** : vérification/receive CAS, présent dans l'ISO de secours.

## Avant la panne

1. Relever partitions, montages, UUID, EFI, sous-volumes et modes d'amorçage. **S'il existe LUKS, RAID/LVM, plusieurs sous-volumes montés, Secure Boot ou une autre topologie, arrêter : non certifié.**
2. Sauvegarder la racine Btrfs en lecture seule, vérifier le flux complet avec **harbor-transport verify-stream**, archiver l'ESP avec empreinte SHA-256.
3. Préparer explicitement les fichiers ReaR à partir des exemples et un profil **root-owned**. Les archives doivent être accessibles **depuis le système de secours**, pas uniquement sur le disque à remplacer.
4. Exécuter **rear -v mkrescue**, vérifier que l'ISO contient binaires, profil, dépôt et EFI. Conserver cet ISO et en vérifier le SHA-256.
5. **Répéter sur une VM avec disque vierge**, avant de décider si une restauration physique est envisageable.

## Restaurer

1. Démarrer la VM cible sur l'ISO ReaR ; vérifier soigneusement l'unique disque **virtu el** destiné à être effacé et le plan de partitions ReaR.
2. Utiliser **rear -v recover**. ReaR recrée GPT, ESP, Btrfs, swap et monte la nouvelle racine dans /mnt/local.
3. EXTERNAL_RESTORE invoque Harbor ; le script refuse les montages/répertoires incohérents, les archives absentes, une ESP corrompue, les sous-volumes supplémentaires et Secure Boot.
4. Harbor vérifie CAS et SHA-256, reçoit dans un staging, restaure les fichiers Btrfs+EFI, puis réinstalle GRUB standard et fallback en fonction du nouveau disque.
5. Retirer l'ISO, redémarrer **sur le disque restauré** et vérifier Btrfs, ESP, noyau, initramfs et le contenu d'un fichier témoin sauvegardé. Vérifier le code retour réel.

Si la récupération échoue, conserver disque virtuel et logs, analyser **HARBOR_REAR_FAIL** et **rear recover**. Ne jamais désactiver un contrôle d'intégrité pour obtenir un faux succès.

Documentation ReaR officielle : https://relax-and-recover.org/rear-user-guide/basics/configuration.html
