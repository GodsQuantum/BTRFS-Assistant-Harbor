# QA multi-distributions — upgrade et retour arrière des paquets

**Candidat alpha9 révisé, 21 octobre 2026.** Ce document ne transforme pas une archive QA en release stable.

## Pourquoi une version de paquet distincte

Le dernier candidat GitHub modifie la sécurité du catalogue CAS multimachine et ajoute les tests de concurrence. Réutiliser les numéros de versions du candidat précédent empêcherait les gestionnaires de paquets de reconnaître une véritable mise à jour.

| Distribution | Paquet de référence | Nouveau candidat |
| --- | --- | --- |
| Debian 13 | `0.1.0~alpha9-11+deb13` | `0.1.0~alpha9-12+deb13` |
| Fedora 44 | `0.1.0-0.alpha9.10` | `0.1.0-0.alpha9.12` |
| Arch/CachyOS | `0.1.0alpha9-4` | `0.1.0alpha9-12` |

Les deux workflows GitHub existants (certification.yml et native-packages.yml) effectuent automatiquement ces comparaisons sur la branche de certification. Ils téléchargent les artefacts de référence et vérifient SHA256SUMS avant installation. Baselines : 39654023427 pour Debian et 39654023512 pour Fedora et Arch. Le nouveau paquet est construit dans le meme job.

Pour chaque distribution, un conteneur jetable effectue : installation ancienne → mise à niveau vers le candidat → validation du binaire installé → retour arrière ancien → remontée au candidat → désinstallation. Le test refuse si la version annoncée n'est pas réellement supérieure ou si les empreintes ne correspondent pas. Tout échec conserve le code de sortie du runner.

### Limites et sécurité

- Ces contrôles sont automatiques sur la branche QA. Les artefacts historiques expirent, donc toute expiration doit produire un échec explicite et une nouvelle référence archivée sera nécessaire. Sur les autres branches, cette étape historique est sautée par condition.
- Il s'agit de changements de *paquets* sans redémarrage du système, pas de migration de données personnelles ni d'un redémarrage après panne.
- Ces tests ne certifient pas un noyau personnalisé, le matériel physique Pegasus, Galactica/macOS, LUKS/RAID/Secure Boot ou le GC destructif sur stockage NAS.
- Ne jamais rétrograder les données utilisateur CAS sans preuve de compatibilité ; les manifestes legacy restent lisibles et aucune migration destructive n'est déclenchée automatiquement.
- Le dépôt `Workstations/` reste commun, `objects/` partagé, `machines/<machine>/manifests/` indépendants.

**Décision :** QA candidate jusqu'à production d'un run de mise à jour complet et vérifié sur le même code que les autres workflows de certification.
