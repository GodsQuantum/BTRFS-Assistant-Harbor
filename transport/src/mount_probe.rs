//! Read the kernel mount table without a distro-specific findmnt executable.
//! This is a preflight guard; the repository UUID is checked separately.
use anyhow::{Context, Result, bail, ensure};
use std::path::Path;

fn decode_mountinfo_path(input: &str) -> String {
    let mut decoded = input.to_string();
    for (encoded, decoded_char) in [
        ("\\040", " "),
        ("\\011", "\t"),
        ("\\012", "\n"),
        ("\\134", "\\"),
    ] {
        decoded = decoded.replace(encoded, decoded_char);
    }
    decoded
}

pub fn filesystem_for_path(path: &Path, mountinfo: &str) -> Result<String> {
    ensure!(path.is_absolute(), "mount probe path must be absolute");
    let mut winner: Option<(usize, &str)> = None;
    for line in mountinfo.lines() {
        let tokens: Vec<_> = line.split_whitespace().collect();
        if tokens.len() < 8 || tokens[4].is_empty() {
            continue;
        }
        let Some(separator) = tokens.iter().position(|token| *token == "-") else {
            continue;
        };
        if separator + 2 >= tokens.len() {
            continue;
        }
        let mountpoint = decode_mountinfo_path(tokens[4]);
        let mounted = Path::new(&mountpoint);
        if mounted.is_absolute() && path.starts_with(mounted) {
            let length = mounted.components().count();
            if winner.is_none_or(|(current, _)| length > current) {
                winner = Some((length, tokens[separator + 1]));
            }
        }
    }
    match winner {
        Some((_, kind)) => Ok(kind.to_string()),
        None => bail!("no matching kernel mount record; refusing backup"),
    }
}

pub fn actual_filesystem(path: &Path) -> Result<String> {
    let canonical = path
        .canonicalize()
        .context("mount destination not accessible")?;
    ensure!(canonical.is_dir(), "mount destination is not a directory");
    let table = std::fs::read_to_string("/proc/self/mountinfo")
        .context("cannot read kernel mount table")?;
    filesystem_for_path(&canonical, &table)
}
