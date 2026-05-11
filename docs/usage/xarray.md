# Using with xarray

## Writing a dataset

```python
import numpy as np
import xarray as xr
from zarrswift import SwiftStore

storage_options = {
    "preauthurl": "https://swift.example.org/v1/AUTH_...",
    "preauthtoken": "...",
}

store = await SwiftStore.open(
    container="my-container",
    prefix="xarray-demo",
    storage_options=storage_options,
)

ds = xr.Dataset(
    {"temperature": (("time", "lat", "lon"), np.random.rand(12, 180, 360))},
    coords={
        "time": np.arange(12),
        "lat": np.linspace(-90, 90, 180),
        "lon": np.linspace(-180, 180, 360),
    },
)
ds.to_zarr(store=store, mode="w", consolidated=True)
```

## Reading a dataset

```python
store = await SwiftStore.open(
    container="my-container",
    prefix="xarray-demo",
    storage_options=storage_options,
)

ds = xr.open_zarr(store=store, consolidated=True)
print(ds)
```

!!! tip
    Use `consolidated=True` for large datasets — it caches all metadata in a
    single `.zmetadata` object, avoiding many small HTTP requests on open.
