# Contributing to Btrfs Assistant Harbor

Thank you for improving native Linux Btrfs backups. ⚓

1. Open an issue describing a reproducible problem, the OS, kernel, Btrfs version and Snapper configuration, **without uploading private backup data**.
2. Use a feature branch and keep Qt/C++, Rust/CAS and packaging changes separately reviewable.
3. Run `cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release`, `cmake --build build`, `QT_QPA_PLATFORM=offscreen ctest --test-dir build --output-on-failure`, `cargo test --locked --manifest-path transport/Cargo.toml --all-targets`, and `python3 -m unittest discover -s tests -p "test_*.py"`.
4. Keep QA on disposable loopback Btrfs and QEMU guests; do **not** modify mounted user repositories, snapshots, encrypted disks or real backups in tests.
5. Preserve the **disabled destructive NAS CAS GC** until robust distributed locking is proven.
6. Provide English strings with French/Chinese Qt catalog updates; never announce unsupported topologies as certified.
7. Preserve upstream **Btrfs Assistant GPL-3.0-or-later** attribution and bundled third-party licenses.

See [Linux certification scope](docs/validation/QA_LINUX_STABLE_SCOPE_2026-10-22.md) and [brand guide](branding/BRAND.md).
