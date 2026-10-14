# Guide pratique — sauvegarder et restaurer avec Harbor

## 1. Préparer la source

Utiliser un système Btrfs avec **Snapper** : sélectionner un snapshot en lecture seule. Harbor ne doit pas créer à sa place des snapshots locaux parallèles. Vérifier que la destination existe, possède des droits d'écriture contrôlés et assez d'espace libre.

## 2. Sauvegarder depuis l'application

1. Lancer **Btrfs Assistant Harbor** via son icône de bureau.
2. Aller dans **Remote backups**, choisir le moteur **checkpoint v2** (ancien format) ou **Harbor CAS** (format Rust). Les dépôts ne sont pas interchangeables.
3. Sélectionner **Snapper configuration** puis **Readonly snapshot**.
4. Entrer la destination. Pour CAS, sélectionner un répertoire dédié existant et cliquer **Initialize CAS destination**. N'autoriser une destination locale que lorsqu'elle est volontaire.
5. Pour CAS incrémental, choisir explicitement **Incremental parent** ; une chaîne incohérente doit être refusée.
6. Cliquer **Send selected snapshot**, lire la progression et le journal ; cliquer **List remote backups**, sélectionner l'archive et **Verify selected archive**.

## 3. Simuler la récupération

Sélectionner **Recovery staging** : un dossier Btrfs **neuf, vide et distinct du système actif**. Utiliser **Preview recovery**, jamais la racine en cours d'utilisation. Contrôler indépendamment les fichiers reçus. La GUI ne recrée pas les tables de partitions : pour une reprise machine, voir le [guide ReaR](RECUPERATION_REAR_FR.md).

## 4. Planification et rétention

**Enable schedule**, **Scheduled backups** et **Disable schedule** administrent les tâches selon le moteur ; CAS utilise les snapshots déjà existants de Snapper. **Delete selected CAS backup** et **Reclaim unused CAS chunks** démarrent en simulation : inspecter les archives retenues, parents et blocs partagés, puis confirmer le plan précis. Aucune suppression ne doit être forcée sur des dépôts NFS/SMB non certifiés.

## 5. Sauvegarde machine historique

**Audit backup coverage** inspecte la couverture, **List machine backup sets** liste les anciens jeux, **Preview staged machine restore** examine un staging. Un inventaire complet ne prouve pas un disque amorçable : il faut tester EFI/GRUB en VM.

## 6. Diagnostics usuels

- **Backend not trusted** : le CLI doit être installé par le paquet dans un chemin contrôlé par root, sans écriture possible pour les groupes/utilisateurs ordinaires.
- **Invalid destination** : utiliser un chemin absolu existant avec droits adaptés.
- **No Btrfs filesystems found** : vérifier les montages ; ne jamais supprimer ce garde-fou.
- **Transfert réseau interrompu** : consulter la raison et tester ACL/UID sans changer arbitrairement les montages Cloud9/serveur.

Les [preuves et limites](../VALIDATION.md) distinguent tests automatisés et tests physiques non réalisés.
