# QA sécurité — Snapper sans shell (Codespaces, 21 octobre 2026)

L'ancien adaptateur Snapper construisait des chaînes à partir du nom de configuration, de chemins Btrfs et de descriptions, puis les transmettait à `System::runCmd(QString)`, qui utilise `bash -c`. Une apostrophe ou un métacaractère dans la description d'un snapshot pouvait donc être interprété comme une commande. **La version stable ne doit pas conserver ce chemin de code.**

## Modifications

- Toutes les opérations de `src/util/Snapper.cpp` et `src/util/Snapper.h` passent désormais un `QStringList` de paramètres séparés à `System::runCmd(executable, argv)`, lui-même fondé sur `QProcess::start(executable, arguments)`.
- Les options de l'exécutable configuré (`/usr/bin/snapper`, éventuellement `--no-dbus`) sont découpées une seule fois par `QProcess::splitCommand`. Les données utilisateurs ne sont plus assemblées dans un script shell.
- Opérations traitées : create-config, création et modification de description, modification de rétention/configuration, nettoyage, suppression, liste, inventaire et restauration contextuelle.
- La logique de sortie CSV Snapper est conservée (code retour, suppression de la première ligne d'en-tête).
- Le banc d'intégration Snapper + Qt utilise deux snapshots natifs pré/post dans une image Btrfs jetable, puis tente une troisième création avec une description de type `Harbor QA ' ; touch <chemin-jouet>; #`. La certification exige que la description soit conservée *verbatim*, qu'aucun fichier extérieur ne soit créé et que le snapshot supplémentaire soit supprimé.

## Portes de certification

Le projet ne saurait déclarer G10/G20 complets avant succès des suites Qt du commit exact, du test Snapper natif et des autres workflows GitHub. Les tests antérieurs au correctif ne sont pas des preuves du nouveau binaire. La correction n'implique ni changement de fichiers système sur Cloud9 ni accès à des montages/données de sauvegarde réels. L'hôte n'est utilisé que pour joindre Codespaces et synchroniser les commits GitHub.

**Limites** : ce correctif ne prouve pas la sécurité de toutes les autres commandes système héritées de Btrfs Assistant qui pourraient utiliser l'ancien surchargement `System::runCmd(QString)`. Les fonctionnalités non testées sur matériel réel, Secure Boot, LUKS/RAID et macOS/APFS restent exclues.
