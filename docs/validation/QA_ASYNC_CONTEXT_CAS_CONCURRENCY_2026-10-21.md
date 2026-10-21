# QA — Protection des sélections multimachines et concurrence CAS

**Date : 21 octobre 2026.** Tests dans GitHub Codespaces sur données synthétiques et chemins temporaires uniquement ; aucune opération sur Pegasus/Galactica physiques.

## Risque traité

Une liste de sauvegardes ou un aperçu de suppression/récupération reste asynchrone pendant que l'utilisateur peut modifier le dossier `Workstations/`, l'identité `Pegasus/Galactica`, le moteur ou le chemin de restauration. Sans garde, l'interface peut afficher une liste correspondant à l'ancien dépôt ou demander confirmation pour une archive sélectionnée avant le changement.

## Correction défensive

- Changement de dépôt, identité ou moteur : l'inventaire affiché et les sélections périmées sont effacés.
- Changement du dossier de restauration : l'aperçu en attente est invalidé.
- Chaque réponse asynchrone est liée au dépôt, au nom de machine, au moteur, à la destination de restauration, à l'archive et à **un compteur de révision** : changer puis rétablir les valeurs d'origine n'autorise pas une réponse périmée.
- Les confirmations destructives refusent tout contexte modifié. Le GC sans archive sélectionnée (récupération d'orphelins) reste possible après son propre aperçu.
- La vérification du plan côté moteur et le verrou global du CAS demeurent obligatoires.

## Nouvelles preuves reproductibles

- `tests/test_remote_plan.cpp` : comparaison stricte de contexte dépôt/identité/moteur.
- `tests/test_gui_user_smoke.cpp` : changement d'identité, de dépôt et de moteur efface l'inventaire avant les actions.
- `tests/qa_cas_concurrent_clients.py` : plusieurs processus CLI distincts écrivent des archives dans un **seul** `objects/` partagé ; aucune réplication des objets entre machines. Une nouvelle archive rend le digest du plan GC précédent invalide et la confirmation doit échouer. Après recalcul du plan et GC Pegasus, toutes les archives Galactica restent vérifiables et l'une est restaurée octet pour octet.
- `.github/workflows/certification.yml` : le test de concurrence est intégré à la porte CAS/endurance, en plus des 1 000 cycles.

**Mesure locale initiale (Codespace, avant CI)** : 8 processus concurrents, 20 archives + 1 après l'aperçu, 2 nouveaux objets globaux, 38 réutilisations, rejet du plan GC périmé, restauration SHA-256 concordante (code retour 0). Les résultats GitHub Actions du commit exact restent la condition de publication.

## Limites

Ces tests certifient des processus Linux indépendants partageant un répertoire local et des VM Linux utilisant une destination commune ; ils ne certifient pas le verrou distribué pour un GC destructif sur NFS/SMB ni une sauvegarde macOS/APFS. Le refus de GC destructif réseau est maintenu. Une session de bureau Plasma complète, un vrai appareil, et le traitement des différentes topologies de démarrage restent des domaines d'essais séparés.
