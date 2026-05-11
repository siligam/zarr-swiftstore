# Using with zarr

## Opening a store

```python
import zarr
from zarrswift import SwiftStore

storage_options = {
    "preauthurl": "https://swift.example.org/v1/AUTH_...",
    "preauthtoken": "...",
}

store = await SwiftStore.open(
    container="my-container",
    prefix="zarr-demo",
    storage_options=storage_options,
)
```

The `container` is created automatically if it does not exist.

## Writing arrays

```python
root = zarr.open_group(store=store, mode="w")

# Create and write an array
z = root.zeros("data", shape=(1000, 1000), chunks=(100, 100), dtype="f4")
z[:] = 3.14
```

## Reading arrays

```python
root = zarr.open_group(store=store, mode="r")
z = root["data"]
print(z[:10, :10])
```

## Read-only mode

```python
store = await SwiftStore.open(
    container="my-container",
    prefix="zarr-demo",
    storage_options=storage_options,
    read_only=True,
)
```

## Using as a context manager

```python
async with await SwiftStore.open("my-container", storage_options=storage_options) as store:
    root = zarr.open_group(store=store, mode="w")
    root.zeros("data", shape=(100,), dtype="i4")
```
