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

- **S3 compat (`swift3`/`s3api`) is unusable** — signing S3 requests requires a
  username + password (`ST_USER`/`ST_KEY`), but TempAuth deployments typically hand
  out pre-authenticated tokens (`OS_AUTH_TOKEN` + `OS_STORAGE_URL`) that cannot sign
  S3 requests.
- **`s3fs`/`boto3` do not work** for the same reason.
- **`swiftspec`** works in principle but has seen limited maintenance since 2022.

This library uses `python-swiftclient` directly, which speaks the native Swift API
and accepts pre-auth tokens. It is the only actively-maintained, zarr-v3-native
option for these deployments.

**Known deployments where this matters:**

- [DKRZ](https://www.dkrz.de/) (`swift.dkrz.de`) — uses TempAuth, provides pre-auth
  tokens only; S3 compat middleware is present but not accessible without signing
  credentials.

If your OpenStack cluster provides full Keystone and EC2 credentials, you can use
`zarr.storage.FsspecStore` with `swiftspec` or `s3fs` instead.

## Install

```bash
pip install zarr-swiftstore
```

Or from source with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/siligam/zarr-swiftstore.git
cd zarr-swiftstore
uv sync
```

## Usage

### Authentication

Provide credentials as a `storage_options` dict passed to `SwiftStore`.

**Pre-authenticated token** (most common in TempAuth deployments):

```python
import os

storage_options = {
    "preauthurl": os.environ["OS_STORAGE_URL"],
    "preauthtoken": os.environ["OS_AUTH_TOKEN"],
}
```

**Username + password** (TempAuth v1.0):

```python
storage_options = {
    "authurl": "https://swift.example.org/auth/v1.0",
    "user": "{account}:{user}",
    "key": "{password}",
}
```

### zarr

```python
import zarr
from zarrswift import SwiftStore

store = await SwiftStore.open(
    container="my-container",
    prefix="zarr-demo",
    storage_options=storage_options,
)

root = zarr.open_group(store=store, mode="w")
z = root.zeros("foo/bar", shape=(10, 10), chunks=(5, 5), dtype="i4")
z[:] = 42
```

### xarray

```python
import numpy as np
import xarray as xr
from zarrswift import SwiftStore

store = await SwiftStore.open(
    container="my-container",
    prefix="xarray-demo",
    storage_options=storage_options,
)

ds = xr.Dataset(
    {"foo": (("x", "y"), np.random.rand(4, 5))},
    coords={"x": [10, 20, 30, 40], "y": [1, 2, 3, 4, 5]},
)
ds.to_zarr(store=store, mode="w", consolidated=True)

# load
ds = xr.open_zarr(store=store, consolidated=True)
```

### Container utilities (ACLs, TempURLs)

```python
from zarrswift import SwiftStore
from zarrswift.utils import is_public, toggle_public, acquire_token

store = await SwiftStore.open("my-container", storage_options=storage_options)

# Check / toggle public read access
print(is_public(store))   # False
toggle_public(store)
print(is_public(store))   # True
```

## Running the tests

Integration tests require a live Swift service. Set the environment variables
for your deployment and enable the test suite with `ZARR_TEST_SWIFT=1`.

**Pre-auth token:**

```bash
export OS_STORAGE_URL="https://swift.example.org/v1/AUTH_..."
export OS_AUTH_TOKEN="..."
export ZARR_TEST_SWIFT=1
pytest -v zarrswift
```

**Username + password:**

```bash
export ST_AUTH="https://swift.example.org/auth/v1.0"
export ST_USER="{account}:{user}"
export ST_KEY="{password}"
export ZARR_TEST_SWIFT=1
pytest -v zarrswift
```

For local CI without a real Swift cluster, the tests run against
[openstackswift/saio](https://hub.docker.com/r/openstackswift/saio):

```bash
docker run -d -p 8080:8080 openstackswift/saio
export ST_AUTH=http://localhost:8080/auth/v1.0
export ST_USER=test:tester
export ST_KEY=testing
export ZARR_TEST_SWIFT=1
pytest -v zarrswift
```
