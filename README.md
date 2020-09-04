# zarr-swiftstore
openstack swift object storage back-end for zarr


## Install

```bash
python setup.py install
```

or for development version use pip

```bash
pip install -e .
```

If pip is unable to install numcodecs then use conda to install dependencies

```bash
conda env update --file environment.yml
conda activate swiftsotre
python setup.py install
# or
# pip install -e .
```

## Usage

Assuming pre-authenticated token (OS_AUTH_TOKEN) and storage_url (OS_STORAGE_URL) are available in the os.environ

1. using zarr

```pythonw
import zarr
from zarrswiftstore.storage import SwfitStore

store = SwfitStore(container='test', prefix='zarr-demo')
root = zarr.group(store=store, overwrite=True)
z = root.zeros('foo/bar', shape=(10, 10), chunks=(5, 5), dtype='i4')
z[:] = 42
```

2. using xarray
```pythonw
import xarray as xr
import numpy as np
from zarrswiftstore.storage import SwfitStore

ds = xr.Dataset(
        {"foo": (('x', 'y'), np.random.rand(4, 5))},
        coords = {
          'x': [10, 20, 30, 40],
          'y': [1, 2, 3, 4, 5],
        },
}

store = SwfitStore(container='test', prefix='xarray-demo')
ds.to_zarr(store=store, mode='w', consolidated=True)

# load
ds = xr.open_zarr(store=store, consolidated=True)
```






