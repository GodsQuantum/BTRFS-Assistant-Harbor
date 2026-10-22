#!/usr/bin/env bash
# Runs only on disposable GitHub-hosted Ubuntu runner, NEVER Pegasus/Cloud9.
set -Eeuo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d /var/tmp/harbor-systemd-qa-XXXXXXXX)"
SNAP_CONFIG="harbor_ci_disposable"
RUN_UID="$(id -u)"
cleanup() {
  set +e
  if [[ -d /var/lib/btrfs-assistant-harbor/manual-jobs ]]; then
    while IFS= read -r id; do
      sudo systemctl disable --now "btrfs-assistant-harbor-job@$id.service" >/dev/null 2>&1
    done < <(sudo find /var/lib/btrfs-assistant-harbor/manual-jobs -maxdepth 1 -name '*.json' -printf '%f\n' | sed 's/\.json$//')
  fi
  sudo snapper --no-dbus -c "$SNAP_CONFIG" delete-config >/dev/null 2>&1 || true
  sudo umount -l "$WORK/nfs" >/dev/null 2>&1 || true
  sudo umount -l "$WORK/btrfs" >/dev/null 2>&1 || true
  sudo pkill -f "ganesha.nfsd -f $WORK/ganesha.conf" >/dev/null 2>&1 || true
  sudo rm -f /usr/local/bin/btrfs
  sudo rm -f /etc/systemd/system/btrfs-assistant-harbor-job@.service
  sudo systemctl daemon-reload >/dev/null 2>&1 || true
  sudo rm -rf -- "$WORK" /var/lib/btrfs-assistant-harbor/manual-jobs
}
finish() {
  local status=$?
  if [[ "$status" -ne 0 ]]; then
    echo "HARBOR_QA_ERROR exit=$status"
    if [[ -f "$WORK/ganesha.log" ]]; then
      tail -80 "$WORK/ganesha.log" || true
    fi
    sudo journalctl --no-pager -n 50 -u 'btrfs-assistant-harbor-job@*' || true
  fi
  cleanup
  exit "$status"
}
trap finish EXIT
mkdir -p "$WORK"/{export,nfs,btrfs}
chmod 755 "$WORK"
sudo chown "$RUN_UID":"$(id -g)" "$WORK/export"
sudo mkdir -p /run/ganesha
sudo systemctl stop nfs-ganesha 2>/dev/null || true
cat > "$WORK/ganesha.conf" <<EOF
NFS_CORE_PARAM {
    Protocols = 4;
    NFS_Port = 20490;
}
EXPORT {
    Export_Id = 77;
    Path = "$WORK/export";
    Pseudo = "/harborqa";
    Access_Type = RW;
    Protocols = 4;
    Transports = TCP;
    Squash = Root_Squash;
    SecType = sys;
    FSAL { Name = VFS; }
}
EOF
sudo /usr/bin/ganesha.nfsd -f "$WORK/ganesha.conf" -L "$WORK/ganesha.log"
sleep 3
sudo mount -t nfs4 -o vers=4.1,port=20490,proto=tcp,timeo=100,retrans=2 \
    127.0.0.1:/harborqa "$WORK/nfs"
test "$(findmnt -T "$WORK/nfs" -n -o FSTYPE)" = "nfs4"
echo "PASS REAL_NFS4_DISPOSABLE"

sudo install -m 0755 "$REPO_ROOT/backend/manual_jobs.py" /usr/bin/btrfs-assistant-harbor-job
sudo install -m 0644 "$REPO_ROOT/backend/cas_schedule.py" /usr/bin/cas_schedule.py
sudo install -m 0644 "$REPO_ROOT/packaging/systemd/btrfs-assistant-harbor-job@.service" \
    /etc/systemd/system/btrfs-assistant-harbor-job@.service
sudo install -m 0755 "$REPO_ROOT/build/qa-btrfs/harbor-transport" /usr/bin/harbor-transport
sudo systemctl daemon-reload
sudo -u "$(id -un)" /usr/bin/harbor-transport init --repo "$WORK/nfs"
test -f "$WORK/nfs/.harbor-repo-id"

truncate -s 1300M "$WORK/source.btrfs"
sudo mkfs.btrfs -f "$WORK/source.btrfs" >/dev/null
sudo mount -t btrfs -o loop "$WORK/source.btrfs" "$WORK/btrfs"
sudo btrfs subvolume create "$WORK/btrfs/root"
sudo dd if=/dev/urandom of="$WORK/btrfs/root/payload.bin" bs=1M count=384 status=none
sudo snapper --no-dbus -c "$SNAP_CONFIG" create-config -f btrfs "$WORK/btrfs/root"
sudo snapper --no-dbus -c "$SNAP_CONFIG" create -t single -d "Harbor detached QA" >/dev/null
sudo snapper --no-dbus -c "$SNAP_CONFIG" list --disable-used-space

# A real Btrfs send, but deliberately rate limited on disposable runner so
# the Qt window is provably destroyed before transfer completion.
sudo tee /usr/local/bin/btrfs >/dev/null <<'EOF'
#!/bin/bash
set -o pipefail
if [[ "${1:-}" == "send" ]]; then
  /usr/bin/btrfs "$@" | /usr/bin/pv -q -L 12582912
else
  exec /usr/bin/btrfs "$@"
fi
EOF
sudo chmod 755 /usr/local/bin/btrfs
export QT_QPA_PLATFORM=offscreen
export HARBOR_GUI_QA_SYSTEMD_NFS_REPO="$WORK/nfs"
export HARBOR_GUI_QA_SYSTEMD_SNAPPER_CONFIG="$SNAP_CONFIG"
sudo --preserve-env=QT_QPA_PLATFORM,HARBOR_GUI_QA_SYSTEMD_NFS_REPO,HARBOR_GUI_QA_SYSTEMD_SNAPPER_CONFIG \
    env PKEXEC_UID="$RUN_UID" "$REPO_ROOT/build/qa-btrfs/src/test-harbor-gui-user-smoke" \
    manualCasButtonSurvivesActualQtWindowDestruction
echo "PASS QT_GUI_WINDOW_DESTROYED_JOB_WAS_ACTIVE"

ID="$(sudo find /var/lib/btrfs-assistant-harbor/manual-jobs -maxdepth 1 \
    -name '*.json' -printf '%f\n' | sed 's/\.json$//' | head -1)"
test -n "$ID"
STATE=""
for step in $(seq 1 160); do
    STATE="$(sudo python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["state"])' \
         "/var/lib/btrfs-assistant-harbor/manual-jobs/$ID.json")"
    if [[ "$STATE" == "completed" ]]; then
        break
    fi
    if [[ "$STATE" == "cancelled" || "$STATE" == "failed" ]]; then
        sudo journalctl -u "btrfs-assistant-harbor-job@$ID" --no-pager -n 65
        exit 1
    fi
    sleep 3
done
if [[ "$STATE" != completed ]]; then
    sudo journalctl -u "btrfs-assistant-harbor-job@$ID" --no-pager -n 100
    echo "FAIL BACKGROUND_TRANSFER_TIMEOUT"
    exit 1
fi
echo "PASS SYSTEMD_COMPLETED_AFTER_GUI_CLOSE"
ARCHIVE="$(sudo python3 -c 'import sys;sys.path.insert(0,"/usr/bin");from importlib.machinery import SourceFileLoader; mod=SourceFileLoader("manual_jobs","/usr/bin/btrfs-assistant-harbor-job").load_module(); print(mod.recorded_archive(mod.load(sys.argv[1])))' "$ID")"
sudo env PKEXEC_UID="$RUN_UID" /usr/bin/harbor-transport verify-stream \
    --repo "$WORK/nfs" --name "$ARCHIVE"
sudo mkdir -p "$WORK/btrfs/staging"
sudo env PKEXEC_UID="$RUN_UID" /usr/bin/harbor-transport receive \
    --repo "$WORK/nfs" --name "$ARCHIVE" --staging "$WORK/btrfs/staging" --confirm
sudo cmp "$WORK/btrfs/root/payload.bin" "$WORK/btrfs/staging/snapshot/payload.bin"
echo "PASS VERIFIED_RESTORED_MATCHES_SOURCE"
