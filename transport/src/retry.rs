//! Narrow, bounded retry policy for transient network/filesystem operations.
//! Permanent identity or integrity mismatches fail immediately.
use anyhow::{Result, ensure};
use std::io;

pub struct RetryOutcome<T> {
    pub value: T,
    pub retries: u32,
}

fn is_transient(error: &anyhow::Error) -> bool {
    error.chain().any(|cause| {
        cause.downcast_ref::<io::Error>().is_some_and(|error| {
            matches!(
                error.raw_os_error(),
                Some(110 | 104 | 107 | 113 | 116 | 112)
            )
        })
    })
}

pub fn retry_transient<T>(
    retries: u32,
    mut operation: impl FnMut() -> Result<T>,
    mut wait: impl FnMut(u64),
) -> Result<RetryOutcome<T>> {
    ensure!(retries <= 240, "retry count exceeds safety limit");
    for attempt in 0..=retries {
        match operation() {
            Ok(value) => {
                return Ok(RetryOutcome {
                    value,
                    retries: attempt,
                });
            }
            Err(error) if is_transient(&error) && attempt < retries => {
                let seconds = (1u64 << attempt.min(6)).min(60);
                wait(seconds);
            }
            Err(error) => return Err(error),
        }
    }
    unreachable!("bounded retry loop returns on final attempt")
}
