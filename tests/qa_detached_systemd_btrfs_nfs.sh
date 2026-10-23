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
sudo systemctl stop nfs-ganesha 2>/dev/null || true
# systemd removes RuntimeDirectory on stop; create the PID directory AFTER.
sudo mkdir -p /var/run/ganesha
cat > "$WORK/ganesha.conf" <<EOF
NFS_CORE_PARAM {
    Protocols = 4;
    NFS_Port = 20490;
    # This disposable loopback-only server must not compete with any
    # preexisting runner RQUOTA service on its standard port (875).
    Rquota_Port = 30875;
    Bind_Addr = 127.0.0.1;
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
sudo timeout 30s mount -t nfs4 -o vers=4.1,port=20490,proto=tcp,timeo=30,retrans=1,soft \
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
echo "HARBOR_QA_DESKTOP_LIST_BEFORE_CLICK"
sudo -u "$(id -un)" /usr/bin/harbor-transport list --repo "$WORK/nfs"
echo "HARBOR_QA_POLKIT_ROOT_SQUASH_LIST_BEFORE_CLICK"
sudo env PKEXEC_UID="$RUN_UID" /usr/bin/harbor-transport list --repo "$WORK/nfs"
echo "PASS CAS_INVENTORY_WITH_ORIGINAL_FSUID"

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
JOB_FILE="/var/lib/btrfs-assistant-harbor/manual-jobs/$ID.json"
UNIT="btrfs-assistant-harbor-job@$ID.service"
# Crash the SUPERVISED Python process after at least one real source chunk
# has been ingested, but only in this disposable GitHub runner fixture.
# The Qt window was ALREADY destroyed above.
SAW_PROGRESS=false
for step in $(seq 1 35); do
    STATE="$(sudo python3 -c 'import json,sys; x=json.load(open(sys.argv[1])); print(x["state"],x.get("bytes_read",0))' "$JOB_FILE")"
    read -r job_state bytes_read <<< "$STATE"
    if [[ "$job_state" == "running" && "$bytes_read" -gt 1048576 ]]; then
        SAW_PROGRESS=true
        break
    fi
    sleep 1
done
if [[ "$SAW_PROGRESS" != true ]]; then
    echo "FAIL_NO_LIVE_CAS_PROGRESS_BEFORE_CRASH"
    sudo journalctl -u "$UNIT" --no-pager -n 80 || true
    exit 1
fi
sudo systemctl kill --kill-whom=main --signal=SIGKILL "$UNIT"
echo "PASS SUPERVISED_JOB_SIGKILL_IN_PROGRESS"
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
ATTEMPTS="$(sudo python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["attempts"])' "$JOB_FILE")"
test "$ATTEMPTS" -ge 2
echo "PASS SYSTEMD_RESTART_AFTER_SIGKILL attempts=$ATTEMPTS"
ARCHIVE="$(sudo python3 -c 'import sys;sys.path.insert(0,"/usr/bin");from importlib.machinery import SourceFileLoader; mod=SourceFileLoader("manual_jobs","/usr/bin/btrfs-assistant-harbor-job").load_module(); print(mod.recorded_archive(mod.load(sys.argv[1])))' "$ID")"
sudo env PKEXEC_UID="$RUN_UID" /usr/bin/harbor-transport verify-stream \
    --repo "$WORK/nfs" --name "$ARCHIVE"
sudo mkdir -p "$WORK/btrfs/staging"
sudo env PKEXEC_UID="$RUN_UID" /usr/bin/harbor-transport receive \
    --repo "$WORK/nfs" --name "$ARCHIVE" --staging "$WORK/btrfs/staging" --confirm
sudo cmp "$WORK/btrfs/root/payload.bin" "$WORK/btrfs/staging/snapshot/payload.bin"
echo "PASS VERIFIED_RESTORED_MATCHES_SOURCE"
# Loss of the actual NFS4 mount must NEVER cause a local-directory fallback.
sudo umount "$WORK/nfs"
set +e
sudo env PKEXEC_UID="$RUN_UID" /usr/bin/btrfs-assistant-harbor-job start \
    --repo "$WORK/nfs" --machine HarborQATest --snapper-config "$SNAP_CONFIG" \
    --snapper-number 1 >"$WORK/offline.stdout" 2>"$WORK/offline.stderr"
offline_rc=$?
set -e
if [[ "$offline_rc" -eq 0 ]]; then
    echo "FAIL_CAS_TRANSFER_ACCEPTED_UNMOUNTED_NFS"
    exit 1
fi
echo "PASS LOST_NFS_MOUNT_FAILS_CLOSED"
sudo mount -t nfs4 -o vers=4.1,port=20490,proto=tcp,timeo=30,retrans=1,soft \
     127.0.0.1:/harborqa "$WORK/nfs"
test "$(findmnt -T "$WORK/nfs" -n -o FSTYPE)" = "nfs4"
sudo env PKEXEC_UID="$RUN_UID" /usr/bin/harbor-transport verify-stream \
     --repo "$WORK/nfs" --name "$ARCHIVE"
echo "PASS NFS_REMOUNT_VERIFIED_EXISTING_ARCHIVE"
