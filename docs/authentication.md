# Authentication

Credentials are passed as a `storage_options` dict to `SwiftStore.open()`.
All keys are forwarded directly to `swiftclient.Connection`.

## Pre-authenticated token

The most common setup in TempAuth deployments. A token is obtained out-of-band
(e.g. via `swift-token new` or `swift auth`) and passed directly:

```python
import os

storage_options = {
    "preauthurl": os.environ["OS_STORAGE_URL"],
    "preauthtoken": os.environ["OS_AUTH_TOKEN"],
}
```

Set the environment variables before opening a store:

```bash
export OS_STORAGE_URL="https://swift.example.org/v1/AUTH_..."
export OS_AUTH_TOKEN="..."
```

## Username and password (TempAuth v1.0)

```python
storage_options = {
    "authurl": "https://swift.example.org/auth/v1.0",
    "user": "{account}:{username}",
    "key": "{password}",
}
```

## Acquiring a token programmatically

`zarrswift.utils.acquire_token` exchanges credentials for a pre-auth token and
optionally sets `OS_STORAGE_URL` / `OS_AUTH_TOKEN` in the environment:

```python
from zarrswift.utils import acquire_token

auth = acquire_token(
    authurl="https://swift.example.org/auth/v1.0",
    user="myaccount:myuser",
    key="mypassword",
    update_env=True,   # sets OS_STORAGE_URL and OS_AUTH_TOKEN
)
# auth = {"preauthurl": "...", "preauthtoken": "..."}
```

!!! note
    `acquire_token` requires the optional `requests` dependency.
