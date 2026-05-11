# API Reference

## SwiftStore

```python
class SwiftStore(zarr.abc.store.Store)
```

zarr v3 storage backend for OpenStack Swift Object Storage.

### Constructor

```python
SwiftStore(
    container: str,
    prefix: str = "",
    storage_options: dict | None = None,
    *,
    read_only: bool = False,
)
```

Use `SwiftStore.open()` rather than the constructor directly — `open()` calls
`_open()` which ensures the container exists.

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `container` | `str` | Swift container name. Created on `open()` if it does not exist. |
| `prefix` | `str` | Optional path prefix inside the container. |
| `storage_options` | `dict` | Keyword arguments forwarded to `swiftclient.Connection`. |
| `read_only` | `bool` | Open in read-only mode (default: `False`). |

### Class attributes

| Attribute | Value |
|-----------|-------|
| `supports_writes` | `True` |
| `supports_deletes` | `True` |
| `supports_listing` | `True` |

### Methods

#### `open` (classmethod)

```python
store = await SwiftStore.open(container, prefix="", storage_options=None, read_only=False)
```

Open the store, creating the Swift container if it does not exist.

#### `get`

```python
value = await store.get(key, prototype, byte_range=None)
```

Retrieve an object. Returns `None` if the key does not exist.
Supports `RangeByteRequest`, `OffsetByteRequest`, and `SuffixByteRequest`.

#### `set`

```python
await store.set(key, value)
```

Write a buffer to Swift.

#### `delete`

```python
await store.delete(key)
```

Delete an object. Idempotent — does not raise if the key does not exist.

#### `exists`

```python
exists = await store.exists(key)
```

Return `True` if the key exists (uses a Swift HEAD request).

#### `list`

```python
async for key in store.list():
    ...
```

Iterate all keys in the store.

#### `list_prefix`

```python
async for key in store.list_prefix(prefix):
    ...
```

Iterate all keys under a prefix.

#### `list_dir`

```python
async for name in store.list_dir(prefix):
    ...
```

Iterate one level of the virtual directory hierarchy (uses Swift `delimiter="/"`).

#### `getsize`

```python
size = await store.getsize(key)
```

Return the byte size of an object using a Swift HEAD request (no download).
Raises `FileNotFoundError` if the key does not exist.

#### `with_read_only`

```python
ro_store = store.with_read_only(read_only=True)
```

Return a new store instance with the same connection but different `read_only` flag.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `url` | `str` | Public URL of the store root (`{swift_url}/{container}/{prefix}`). |
| `container` | `str` | Container name. |
| `prefix` | `str` | Path prefix (empty string if none). |
| `storage_options` | `dict` | Connection options passed to `swiftclient.Connection`. |
| `conn` | `swiftclient.Connection` | Live connection object. |

---

## zarrswift.utils

### `acquire_token`

```python
auth = acquire_token(authurl, user, key=None, update_env=True)
```

Authenticate via TempAuth v1.0 and return `{"preauthurl": ..., "preauthtoken": ...}`.
If `update_env=True`, also sets `OS_STORAGE_URL` and `OS_AUTH_TOKEN`.

### `is_public`

```python
public = is_public(store)
```

Return `True` if the container has `.r:*` in its `X-Container-Read` ACL.

### `toggle_public`

```python
toggle_public(store)
```

Add `.r:*,.rlistings` to the container ACL if absent; remove it if present.

### `getenv_auth`

```python
auth = getenv_auth()
```

Read Swift credentials from environment variables (`OS_STORAGE_URL`,
`OS_AUTH_TOKEN`, `ST_AUTH`, `ST_USER`, `ST_KEY`) and return a `storage_options` dict.
Raises `ValueError` if no variables are set.
