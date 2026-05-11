# Container Utilities

`zarrswift.utils` provides Swift-native helpers for container access control.

## Checking public access

```python
from zarrswift import SwiftStore
from zarrswift.utils import is_public

store = await SwiftStore.open("my-container", storage_options=storage_options)
print(is_public(store))   # False
```

## Toggling public read access

```python
from zarrswift.utils import toggle_public

toggle_public(store)      # make public
print(is_public(store))   # True

toggle_public(store)      # make private again
print(is_public(store))   # False
```

Making a container public sets `X-Container-Read: .r:*,.rlistings`, which allows
unauthenticated HTTP GET access to all objects and listings. Toggling back removes
the ACL entry.

!!! warning
    Public containers are readable by anyone with the URL. Only use this for
    datasets you intend to share openly.

## Acquiring a token

```python
from zarrswift.utils import acquire_token

auth = acquire_token(
    authurl="https://swift.example.org/auth/v1.0",
    user="myaccount:myuser",
    key="mypassword",
)
# Returns {"preauthurl": "...", "preauthtoken": "..."}
# Also sets OS_STORAGE_URL and OS_AUTH_TOKEN in the environment by default
```
