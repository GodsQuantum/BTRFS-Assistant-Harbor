# Btrfs Assistant Harbor alpha9 — ReaR 2.9 R7b, certification QEMU

Date : 14 octobre 2026, Cloud9 / CT700 DEV, NVMe. Résultat : PASS dans la topologie indiquée uniquement.

## Preuve de bout en bout

- VM source Debian 13 amd64, UEFI OVMF, système GPT avec racine Btrfs et ESP vfat.
- ReaR 2.9 (Debian trixie-backports), BACKUP=EXTERNAL, crée un véritable ISO UEFI intégrant le binaire statique Harbor CAS, le manifeste et les objets de sauvegarde, l'archive ESP, sa somme SHA-256, le script Harbor du fork et son validateur de chemins tar.
- ISO R7b : SHA-256 4d0407866253ab2a7b61bcb00c89998240ad543429f662d8d58807f1a8414ed6. Même condensat sur la copie source et la copie QA, 741382144 octets. Le GRUB de l'ISO utilise GRUB2_DEFAULT_BOOT=rear, avec démarrage UEFI non-Secure-Boot automatique, sans sélection manuelle.
- Le disque cible est un fichier image vierge de 7 GiB nommé recovered-debian-r7b.raw. QEMU est configuré sans autre disque en écriture ; l'ISO est en lecture seule. La confirmation ReaR désigne explicitement /dev/vda.
- ReaR 2.9 a recréé la table GPT, l'ESP VFAT, la racine Btrfs, le swap et les montages. EXTERNAL_RESTORE a invoqué le hook du fork ; les journaux indiquent Running external restore command puis Finished external restore command, et enfin Finished recover.
- Harbor a vérifié l'archive Btrfs CAS, prévisualisé sa réception, reçu son sous-volume, validé l'archive EFI, et le hook a installé les GRUB EFI standard et de secours sur le système restauré.
- La VM de secours a été arrêtée normalement ; démarrage distinct du disque restauré SEUL, sans ISO, en conservant les variables OVMF issues de la récupération.
- Debian 13 restauré a atteint le login. Commande de contrôle exécutée dans cet OS avec echo terminal désactivé : HARBOR_REAL_REAR_PRODUCT_R7B_FULL_UEFI_BTRFS_NO_ISO_REBOOT_RC:0.
- Racine /dev/vda2 Btrfs, /boot/efi /dev/vda1 VFAT, fichier original /etc/harbor-qa-marker correct, vmlinuz/initrd retrouvés, deux binaires GRUB EFI présents et de SHA-256 identique : 5263b51d325c20726ed7ecd88ba973867d302da5ce5d1487ce56f4b7efab4884.

## Régressions / builds

- 46/46 tests Python sur le Python venv du chantier (dont les tests ReaR et 8 tests tar malveillant / chemin légitime).
- 50/50 tests Rust release musl ; clippy --all-targets -D warnings PASS ; cargo fmt --check PASS.
- Qt Release / CMake / Ninja et 4/4 tests CTest PASS ; installation DESTDIR dans le répertoire de validation QA PASS, avec btrfs-assistant-harbor, harbor-transport, le hook ReaR, le validateur tar et les exemples de configuration.
- Le code testé et l'ISO QA portent les mêmes sommes SHA-256 : hook ef381b9dcbc9f2db425ecee9c997b4c6fcd1fc87d1370bd5a285d3ae5117069e, helper 9a077f9f76f5895935367df8b8cc363f2600465c06694f84397c78f91b79a055.

## Traçabilité privée sur DEV700

- QA root : /home/arezki/Projets/HomeLab/BTRFS Harbor/qa-vm-rear-alpha9/
- Journal secours : rear-r7b-console.log
- Journal boot sans ISO : boot-r7b-console.log
- ISO : share/rear-debian13-product-r7b.iso
- Contrôle des condensats : share/rear-r7b-two-copy-sha256.log
- Compilation et tests : verification-r7/{python-venv-all.log,rust-release-tests.log,rust-clippy.log,rust-fmt.log,qt-config.log,qt-build.log,qt-ctest.log,install-stage.log}
- Historique des échecs et correctifs R1–R7b : ALPHA9_JOURNAL_CONTINU.md et ALPHA9_RECHERCHES_WEB.md dans le projet NVMe.
- Les images disque et les journaux QA restent hors du Git public. Aucune sauvegarde réelle, mount NFS, configuration Snapper de production, ni Pegasus ne sont modifiés.

## Conditions et limites de la certification

Le scénario démontré couvre UNIQUEMENT une machine x86-64 UEFI, Secure Boot désactivé, un volume racine Btrfs unique, une partition ESP VFAT et GRUB. Le hook d'installation est opt-in : CMake installe les modèles de configuration sous /usr/share/btrfs-harbor/rear/ sans activer /etc/rear/local.conf et sans lancer de récupération sur l'hôte.

NON CERTIFIÉS : Secure Boot activé, LUKS, RAID/LVM, multiples volumes, sous-volumes Btrfs indépendants, systèmes non-Debian, et restauration d'une machine physique. Le script refuse certaines topologies non qualifiées au lieu de les restaurer partiellement. Ne pas utiliser comme seule copie de sauvegarde tant qu'une restauration personnelle n'a pas été testée.

La certification ReaR d'une topologie n'est pas une garantie de fiabilité générale de toute l'application.
