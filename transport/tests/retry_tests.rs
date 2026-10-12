use anyhow::{Result, anyhow};
use harbor_transport::retry::{RetryOutcome, retry_transient};
use std::io;

#[test]
fn backoff_after_transient_nfs_disconnect_then_succeeds() {
    let mut calls = 0;
    let mut waited = vec![];
    let result: Result<RetryOutcome<usize>> = retry_transient(
        8,
        || {
            calls += 1;
            if calls <= 2 {
                return Err(io::Error::from_raw_os_error(110).into());
            }
            Ok(calls)
        },
        |seconds| waited.push(seconds),
    );
    let value = result.unwrap();
    assert_eq!(value.value, 3);
    assert_eq!(value.retries, 2);
    assert_eq!(waited, vec![1, 2]);
}

#[test]
fn permanent_source_uuid_mismatch_is_never_retried() {
    let mut calls = 0;
    let result: Result<RetryOutcome<()>> = retry_transient(
        100,
        || {
            calls += 1;
            Err(anyhow!("snapshot identity changed"))
        },
        |_| panic!("must not wait for permanent errors"),
    );
    assert!(result.is_err());
    assert_eq!(calls, 1);
}

#[test]
fn timeout_failure_has_finite_attempt_limit() {
    let mut calls = 0;
    let mut waited = vec![];
    let result: Result<RetryOutcome<()>> = retry_transient(
        2,
        || {
            calls += 1;
            Err(io::Error::from_raw_os_error(110).into())
        },
        |seconds| waited.push(seconds),
    );
    assert!(result.is_err());
    assert_eq!(calls, 3);
    assert_eq!(waited, vec![1, 2]);
}

#[test]
fn stale_estale_errors_are_retryable_but_permission_errors_fail_closed() {
    let transient: Result<RetryOutcome<()>> =
        retry_transient(1, || Err(io::Error::from_raw_os_error(116).into()), |_| {});
    assert!(transient.is_err());
    let mut calls = 0;
    let denied: Result<RetryOutcome<()>> = retry_transient(
        20,
        || {
            calls += 1;
            Err(io::Error::from_raw_os_error(13).into())
        },
        |_| panic!("permission denied must not retry"),
    );
    assert!(denied.is_err());
    assert_eq!(calls, 1);
}

#[test]
fn upper_bound_prevents_accidental_unbounded_retries() {
    let mut calls = 0;
    let attempted: Result<RetryOutcome<()>> = retry_transient(
        1000,
        || {
            calls += 1;
            Ok(())
        },
        |_| {},
    );
    assert!(attempted.is_err());
    assert_eq!(calls, 0);
}

#[test]
fn transient_cifs_eagain_after_server_restart_is_retried() {
    let mut attempt = 0;
    let result: Result<RetryOutcome<&str>> = retry_transient(
        3,
        || {
            attempt += 1;
            if attempt <= 2 {
                return Err(io::Error::from_raw_os_error(11).into());
            }
            Ok("reconnected")
        },
        |_| {},
    );
    assert_eq!(result.unwrap().value, "reconnected");
    assert_eq!(attempt, 3);
}

#[test]
fn transient_network_eio_is_bounded_and_output_must_still_verify() {
    let mut calls = 0;
    let result: Result<RetryOutcome<()>> = retry_transient(
        1,
        || {
            calls += 1;
            Err(io::Error::from_raw_os_error(5).into())
        },
        |_| {},
    );
    assert!(result.is_err());
    assert_eq!(calls, 2);
}
