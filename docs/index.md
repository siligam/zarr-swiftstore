# zarr-swiftstore

OpenStack Swift object storage backend for [zarr v3](https://zarr.readthedocs.io/).
Enables direct read/write access to zarr datasets stored in Swift containers using
`python-swiftclient` — no S3 compatibility layer required.

## Why this library exists

zarr v3 ships with `FsspecStore`, which supports many cloud backends (S3, GCS, Azure)
through the fsspec ecosystem. For OpenStack Swift specifically, the standard
recommendation is `swiftspec` + `FsspecStore`.

**However, many OpenStack deployments — particularly HPC and research clusters — expose
Swift through TempAuth only, without a full Keystone identity service.** In those
environments:

- **S3 compat (`swift3`/`s3api`) is unusable** — signing S3 requests requires
  EC2-style credentials that TempAuth deployments cannot issue without a Keystone
  identity service.
- **`s3fs`/`boto3` do not work** for the same reason.
- **`swiftspec`** works in principle but has seen limited maintenance since 2022.

This library uses `python-swiftclient` directly, which speaks the native Swift API
and accepts pre-auth tokens. See [ADR 001](adr/001-native-swift-over-s3-compat.md)
for the full investigation.

## Quick start

```python
import zarr
from zarrswift import SwiftStore

store = await SwiftStore.open(
    container="my-container",
    prefix="zarr-demo",
    storage_options={
        "preauthurl": "https://swift.example.org/v1/AUTH_...",
        "preauthtoken": "...",
    },
)

root = zarr.open_group(store=store, mode="w")
z = root.zeros("data", shape=(1000, 1000), chunks=(100, 100), dtype="f4")
z[:] = 3.14
```
