# ADR 001: Use native Swift API rather than fsspec S3 compatibility

**Date:** 2026-05-11
**Status:** Accepted

## Context

zarr v3 ships with `FsspecStore`, which supports many cloud backends through the
fsspec ecosystem. For OpenStack Swift specifically, two generic alternatives exist:

- **`swiftspec` + `FsspecStore`** — an fsspec driver for Swift maintained under the
  fsspec organisation.
- **`s3fs` / `boto3` + `FsspecStore`** — via OpenStack's S3 compatibility middleware
  (`swift3` / `s3api`), which exposes Swift containers as S3 buckets.

We investigated whether either alternative makes zarr-swiftstore redundant.

## Investigation

### swiftspec

`swiftspec` provides an fsspec-compatible Swift driver and is the recommended
generic path for zarr v3 + Swift. It is a valid option for deployments where
Keystone is available and credentials are straightforward.

However, `swiftspec` has seen limited maintenance activity since 2022. For zarr v3
users who need an actively maintained, tested integration, this is a concern.

### S3 compatibility middleware

Many OpenStack deployments run `swift3` or `s3api` middleware, which exposes the
Swift API as an S3-compatible endpoint. If usable, this would allow standard
`s3fs`/`boto3` tooling to work without any Swift-specific library.

**The critical limitation:** S3 compatibility requires signing requests with
AWS-style HMAC credentials (an access key + secret key pair). These come from one
of two sources:

1. **Keystone EC2 credentials** — generated via `openstack ec2 credentials create`.
   Requires a full Keystone identity service.
2. **TempAuth credentials** — the TempAuth username and password used directly as
   the S3 access key and secret key.

In practice, many HPC and research cluster deployments use **TempAuth only**,
without a Keystone identity service. These deployments typically distribute
pre-authenticated tokens (`OS_AUTH_TOKEN` + `OS_STORAGE_URL`) rather than
long-lived username/password pairs.

We tested S3 compat access on such a deployment. Results:

- The S3 middleware was confirmed active (requests received well-formed XML S3
  error responses).
- All credential formats tried (`account:user` / password, username / password)
  returned `403 SignatureDoesNotMatch`.
- A request signed with a completely fabricated key returned the same
  `403 SignatureDoesNotMatch` — the middleware does not distinguish between
  "key not found" and "wrong signature", a common security hardening practice.
- No EC2 credential endpoint was reachable (Keystone not running).
- The OpenStack CLI (`openstack ec2 credentials create`) was not available.

**Conclusion:** On TempAuth-only deployments, the S3 compatibility middleware is
present but not accessible to end users. The TempAuth user database is not wired
into the S3 auth backend, and without Keystone there is no mechanism to generate
EC2 credentials. `s3fs` and `boto3` do not work.

## Decision

Maintain zarr-swiftstore as a native Swift API backend using `python-swiftclient`.

`python-swiftclient` accepts both pre-authenticated tokens and TempAuth v1.0
username/password credentials directly, requiring no S3 compatibility layer.
This is the only reliable path for zarr v3 users on TempAuth-only OpenStack
deployments.

## Consequences

- zarr-swiftstore remains a dependency for users on TempAuth-only deployments.
- Users on full Keystone deployments with EC2 credentials available may prefer
  `zarr.storage.FsspecStore` with `swiftspec` or `s3fs` — this library does not
  compete with that path.
- The `zarrswift.utils` module (`acquire_token`, `toggle_public`, `is_public`)
  provides Swift-native utilities that have no equivalent in the fsspec/S3 path.
