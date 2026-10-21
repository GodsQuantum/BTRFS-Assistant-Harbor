#!/usr/bin/env bash
set -euo pipefail
test -f transport/Cargo.lock
rustc --version
cargo --version
cmake --version | head -n 1
qmake6 --version || true
python3 --version
echo "Codespace ready: local Rust/Qt/Python development. Production certification is gated by CI."
