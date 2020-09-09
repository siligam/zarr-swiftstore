# zarr-swiftstore
openstack swift object storage backend for zarr. It enables direct access to
object storage to read and write zarr datasets.

## Install

```bash
conda create -n swiftstore python=3.6
conda activate swiftstore
pip install git+https://github.com/siligam/zarr-swiftstore.git
```

## Usage

SwiftStore authentication requires (authurl, user, key) or (preauthurl, preauthtoken)
values. Alternative way of providing these values is through environment variables
(ST_AUTH, ST_USER, ST_KEY) or (OS_STORAGE_URL, OS_AUTH_TOKEN).

In the following examples the authentication information is provided through
environment variables.

1. using zarr

```python
import zarr
from zarrswift import SwiftStore

store = SwiftStore(container='demo', prefix='zarr-demo')
root = zarr.group(store=store, overwrite=True)
z = root.zeros('foo/bar', shape=(10, 10), chunks=(5, 5), dtype='i4')
z[:] = 42
```

2. using xarray

```pythonw
import xarray as xr
import numpy as np
from zarrswift import SwiftStore

ds = xr.Dataset(
        {"foo": (('x', 'y'), np.random.rand(4, 5))},
        coords = {
          'x': [10, 20, 30, 40],
          'y': [1, 2, 3, 4, 5],
        },
}

store = SwiftStore(container='demo', prefix='xarray-demo')
ds.to_zarr(store=store, mode='w', consolidated=True)

# load
ds = xr.open_zarr(store=store, consolidated=True)
```

## Test
To run test, set environment variable ZARR_TEST_SWIFT=1
```bash
pytest -v zarrswift
```
