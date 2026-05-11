# Running the Tests

Integration tests require a live Swift service. Enable them with `ZARR_TEST_SWIFT=1`.

## Against a local Swift instance (Docker)

The fastest way to run the full suite locally is with the
[openstackswift/saio](https://hub.docker.com/r/openstackswift/saio) Docker image,
which provides a single-node Swift all-in-one:

```bash
docker run -d -p 8080:8080 openstackswift/saio

export ST_AUTH=http://localhost:8080/auth/v1.0
export ST_USER=test:tester
export ST_KEY=testing
export ZARR_TEST_SWIFT=1

pytest -v zarrswift/tests/test_storage.py
```

## Against a remote Swift service

=== "Pre-auth token"

    ```bash
    export OS_STORAGE_URL="https://swift.example.org/v1/AUTH_..."
    export OS_AUTH_TOKEN="..."
    export ZARR_TEST_SWIFT=1

    pytest -v zarrswift
    ```

=== "Username and password"

    ```bash
    export ST_AUTH="https://swift.example.org/auth/v1.0"
    export ST_USER="{account}:{user}"
    export ST_KEY="{password}"
    export ZARR_TEST_SWIFT=1

    pytest -v zarrswift
    ```

## Expected results

The test suite runs zarr v3's full `StoreTests` class (75 tests). Five sync-API
tests are automatically skipped — they are not applicable to async stores:

```
70 passed, 5 skipped
```
