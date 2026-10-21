# QA multi-distributions — upgrade et retour arrière des paquets

**Candidat alpha9 révisé, 21 octobre 2026.** Ce document ne transforme pas une archive QA en release stable.

## Pourquoi une version de paquet distincte

Le dernier candidat GitHub modifie la sécurité du catalogue CAS multimachine et ajoute les tests de concurrence. Réutiliser les numéros de versions du candidat précédent empêcherait les gestionnaires de paquets de reconnaître une véritable mise à jour.

| Distribution | Paquet de référence | Nouveau candidat |
| --- | --- | --- |
| Debian 13 | `0.1.0~alpha9-11+deb13` | `0.1.0~alpha9-12+deb13` |
| Fedora 44 | `0.1.0-0.alpha9.10` | `0.1.0-0.alpha9.12` |
| Arch/CachyOS | `0.1.0alpha9-4` | `0.1.0alpha9-12` |

Le groupe de tests manuel `.github/workflows/upgrade-compatibility.yml` utilise les artefacts validés et leurs `SHA256SUMS`, conservés sur GitHub Actions. Les runs de référence sont `39654023427` (Debian) et `39654023512` (Fedora et Arch), liés au commit Git `3e273ff`. Les identifiants des deux runs **du candidat nouveau** doivent provenir de workflows entièrement réussis.

Pour chaque distribution, un conteneur jetable effectue : installation ancienne → mise à niveau vers le candidat → validation du binaire installé → retour arrière ancien → remontée au candidat → désinstallation. Le test refuse si la version annoncée n'est pas réellement supérieure ou si les empreintes ne correspondent pas. Tout échec conserve le code de sortie du runner.

### Limites et sécurité

- Le workflow n'est **pas** automatique sur chaque push : les artefacts historiques expirent. Déclencher explicitement un run avec les deux identifiants GitHub des workflows du candidat.
- Il s'agit de changements de *paquets* sans redémarrage du système, pas de migration de données personnelles ni d'un redémarrage après panne.
- Ces tests ne certifient pas un noyau personnalisé, le matériel physique Pegasus, Galactica/macOS, LUKS/RAID/Secure Boot ou le GC destructif sur stockage NAS.
- Ne jamais rétrograder les données utilisateur CAS sans preuve de compatibilité ; les manifestes legacy restent lisibles et aucune migration destructive n'est déclenchée automatiquement.
- Le dépôt `Workstations/` reste commun, `objects/` partagé, `machines/<machine>/manifests/` indépendants.

**Décision :** QA candidate jusqu'à production d'un run de mise à jour complet et vérifié sur le même code que les autres workflows de certification.
