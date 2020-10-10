# zarr-swiftstore
openstack swift object storage backend for zarr. It enables direct access to
object storage to read and write zarr datasets.

## Install

```bash
git clone https://github.com/siligam/zarr-swiftstore.git
cd zarr-swiftstore
python setup.py install
```

## Usage

0. Openstack Swift Object Storage auth_v1.0 requires the following keyword arguments for authentication

For initial authentication:

```python
auth = {
    "authurl": "...",
    "user": "{account}:{user}",
    "key": "{password}",
}
```

or if pre-authenticated token is already available:

```python
auth = {
    "preauthurl": "...",
    "preauthtoken": "...",
}
```

1. using zarr

```python
import os
import zarr
from zarrswift import SwiftStore

auth = {
    "preauthurl": os.environ["OS_STORAGE_URL"],
    "preauthtoken": os.environ["OS_AUTH_TOKEN"],
}

store = SwiftStore(container='demo', prefix='zarr-demo', storage_options=auth)
root = zarr.group(store=store, overwrite=True)
z = root.zeros('foo/bar', shape=(10, 10), chunks=(5, 5), dtype='i4')
z[:] = 42
```

2. using xarray

```python
import xarray as xr
import numpy as np
from zarrswift import SwiftStore

ds = xr.Dataset(
        {"foo": (('x', 'y'), np.random.rand(4, 5))},
        coords = {
          'x': [10, 20, 30, 40],
          'y': [1, 2, 3, 4, 5],
        },
)

store = SwiftStore(container='demo', prefix='xarray-demo', storage_options=auth)
ds.to_zarr(store=store, mode='w', consolidated=True)

# load
ds = xr.open_zarr(store=store, consolidated=True)
```

## Test

Test picks up authentication details from the following environment variables.

If pre-authentication token is already available:

```bash
export OS_AUTH_TOKEN="..."
export OS_STORAGE_URL="..."
```

Otherwise:

```bash
export ST_AUTH="..."
export ST_USER="{account}:{user}"
export ST_KEY="{password}"
```

Also set environment variable ZARR_TEST_SWIFT=1

```bash
export ZARR_TEST_SWIFT=1
pytest -v zarrswift
```
