# Btrfs Assistant Harbor — R26 certification checkpoint (16 octobre 2026)

**Décision : PAS DE VERSION STABLE / NOT PRODUCTION READY.** Branche de certification conservée séparément de la release publique v0.1.0-alpha9 (commit historique 84159a0174c5785c41927d440c81f075f86d21a2).

## Résultats démontrés

- **R26 Rust** : 53 tests all-targets PASS, cargo fmt, clippy strict et build MUSL RC0. SHA binaire MUSL : 8b58055c5116693c90f4fad2255033aed1ce6cb54d34d5814afe30198259ed7d.
- **SMB3** : le défaut EINVAL après reconnexion a été reproduit (r21) puis corrigé sans publier un manifeste incomplet. Retry borné uniquement sur la relecture pré-commit d'objets CIFS, validation complète SHA-256 + BLAKE3 à chaque nouvelle lecture. R22 : coupure avant l'envoi ET pendant un envoi après 3 objets CAS, reconnexion, vérification du flux, restauration comparée octet par octet, RC0. Deux clients indépendants/QEMU CIFS : exclusion flock inter-clients, libération puis réacquisition, RC0. Logs smb-network-cut-r22.log et smb-two-client-lock-r25.log.
- **Debian 13 UEFI Btrfs / X11** : candidat DEB 0.1.0~alpha9-8+deb13, upgrade rev7→rev8→rev7→rev8→purge, 30 commandes invité RC0, QT xcb en français à 125%, QEMU shutdown RC0. SHA DEB 3e1c6151d86b7291eed83343f696f032c15cf3c74a63578dff1c44a1405fb1f3. Trace vm-debian13-current-r8b-lifecycle/qa-results.log.
- **Fedora 44** : paquet RPM R8 compilé avec compilateur natif Fedora 44, CTest 6/6 et Rust PASS en conteneur. SHA RPM e3f0e4bf324fe76e9bc42a935eb25a2e3a73fb182c9b378e341f9ca8f443ca98. L'installation rev8 dans VM Fedora n'a pas été refaite ; le cycle rev7 réel reste PASS.
- **Arch** : paquet rev7 cycle en VM UEFI/Btrfs PASS antérieur. Source/PKGBUILD rev8 préparés, source SHA c9d4e4b9c893717aa84c510e5de53c56db0697b16da1d3ccf9874928a99136a9. Compilation makepkg rev8 **interrompue** à cause de saturation NVMe ; aucun paquet R8 déclaré valide.
- **ReaR R8** : ISO autonome, disque virtuel GPT vierge, Btrfs/VFAT, restauration externe Harbor, GRUB standard/fallback, boot sans ISO, code 0. Seulement une racine Btrfs/une ESP, UEFI x86_64 sans Secure Boot.
- **CAS local** : 3 runs full/incremental/receive, chaînes UUID/parents et corruption fail-closed, GC local preview/confirm avec jetons périmés refusés, parents conservés, SIGKILL durant send après création d'objets puis reprise/restauration comparée (r22) RC0.
- **Snapper** : VM Debian 13, 3 snapshots Btrfs RO → cleanup NUMBER_LIMIT=2 NUMBER_MIN_AGE=0 → 2 snapshots intacts et contents vérifiés, 15 commandes invité RC0, QEMU RC0.
- **NFSv4** : serveur et deux clients virtuels indépendants, flock inter-client PASS. Aucune autorisation GC destructif réseau.
- **GUI** : français complet des chaînes actives, Qt CTest 6/6, Debian13 X11 à 125% avec capture et navigation vers Sauvegardes distantes. Wayland et a11y non testés.

## Portes encore bloquées

G10 parité GUI Btrfs Assistant/Snapper sur toutes fonctions ; G15 powerloss, interruption receive et GC ; G22 annulation/redémarrage GUI ; G23 benchmarks de charge/CPU/RAM/I/O ; G07-G08 vrais cycles rev8 Fedora et Arch ; Ubuntu 26.04, KDE/Wayland. Sans certification, ne pas annoncer ces fonctionnalités comme couvertes.

**Non supportés/refusés par défaut :** Secure Boot, LUKS/RAID/LVM, multi-racines, systemd-boot, firmware physique inconnu, GC CAS destructif sur NFS/SMB. Jamais désactiver les protections pour passer des tests.

## Stockage et nettoyage

Le 16/10, le pool ZFS rpool/nvme-share est arrivé à **100 %**, état critique pour les autres applications Cloud9. Seul le conteneur jetable Arch QA a été arrêté, sortie 137 ; ses logs pré-arrêt sont conservés. Le répertoire Cargo target généré et quatre overlays QEMU feuilles ont été supprimés (logs préservés). Les deux cloud images publiques de Fedora/Arch ont été supprimées après SHA256 vérifiés ; elles sont re-téléchargeables mais devront être revalidées avant tout nouveau run. Les paquets candidats, ISO ReaR, disque restauré, scripts, logs, preuves SHA et worktree Git sont maintenus.

Aucun montage, chemin de production, ACL, SyncBridge, service tiers, snapshot, sauvegarde réelle ou machine Pegasus n'a été modifié. **Pas de release stable tant que le pool n'a pas de marge sûre et que la matrice n'est pas close.**
