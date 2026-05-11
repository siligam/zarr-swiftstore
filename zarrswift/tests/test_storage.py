"""
Integration tests for SwiftStore against a live OpenStack Swift service.

Set ZARR_TEST_SWIFT=1 and the Swift auth environment variables to run:

    export ZARR_TEST_SWIFT=1
    export ST_AUTH=http://localhost:8080/auth/v1.0
    export ST_USER=test:tester
    export ST_KEY=testing
    pytest -v zarrswift/tests/test_storage.py
"""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Any

import pytest
from zarr.core.buffer import Buffer, default_buffer_prototype
from zarr.core.buffer import cpu as cpu_buffer
from zarr.testing.store import StoreTests

from .. import SwiftStore

if TYPE_CHECKING:
    pass

pytestmark = pytest.mark.skipif(
    not os.environ.get("ZARR_TEST_SWIFT"),
    reason="Set ZARR_TEST_SWIFT=1 to run Swift integration tests",
)


class TestSwiftStore(StoreTests[SwiftStore, cpu_buffer.Buffer]):
    store_cls = SwiftStore
    buffer_cls = cpu_buffer.Buffer

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    @pytest.fixture
    def store_kwargs(self) -> dict[str, Any]:
        options = {
            "authurl": os.environ.get("ST_AUTH"),
            "user": os.environ.get("ST_USER"),
            "key": os.environ.get("ST_KEY"),
            "preauthurl": os.environ.get("OS_STORAGE_URL"),
            "preauthtoken": os.environ.get("OS_AUTH_TOKEN"),
        }
        options = {k: v for k, v in options.items() if v}
        return {
            "container": "test_swiftstore",
            "prefix": "test_zarr",
            "storage_options": options,
        }

    @pytest.fixture
    async def store(self, open_kwargs: dict[str, Any]) -> SwiftStore:
        store = await SwiftStore.open(**open_kwargs)
        await store.clear()
        yield store
        await store.clear()
        store.close()

    @pytest.fixture
    async def store_not_open(self, store_kwargs: dict[str, Any]) -> SwiftStore:
        # Open the store to ensure the container exists, then reset _is_open
        # so the test can exercise "not-yet-open" code paths.
        store = await SwiftStore.open(**store_kwargs)
        store._is_open = False
        return store

    # ------------------------------------------------------------------
    # Required abstract test methods
    # ------------------------------------------------------------------

    def test_store_repr(self, store: SwiftStore) -> None:
        assert "SwiftStore" in repr(store)
        assert store.container in repr(store)

    def test_store_supports_writes(self, store: SwiftStore) -> None:
        assert store.supports_writes

    def test_store_supports_listing(self, store: SwiftStore) -> None:
        assert store.supports_listing

    # ------------------------------------------------------------------
    # Required abstract helpers (bypass store API for raw access)
    # ------------------------------------------------------------------

    async def set(self, store: SwiftStore, key: str, value: Buffer) -> None:
        """Write directly to Swift without going through store.set()."""
        full_key = store._full_key(key)
        data = value.to_bytes()
        await asyncio.to_thread(store.conn.put_object, store.container, full_key, data)

    async def get(self, store: SwiftStore, key: str) -> Buffer:
        """Read directly from Swift without going through store.get()."""
        full_key = store._full_key(key)
        _, content = await asyncio.to_thread(
            store.conn.get_object, store.container, full_key
        )
        return cpu_buffer.Buffer.from_bytes(content)

    # ------------------------------------------------------------------
    # SwiftStore-specific tests
    # ------------------------------------------------------------------

    async def test_url(self, store: SwiftStore) -> None:
        assert store.container in store.url
        assert store.prefix in store.url

    async def test_ensure_container(self, store: SwiftStore) -> None:
        import uuid
        new_name = f"test-{uuid.uuid4().hex[:8]}"
        store2 = await SwiftStore.open(
            new_name,
            storage_options=store.storage_options,
        )
        _, listings = await asyncio.to_thread(store2.conn.get_account)
        names = {item["name"] for item in listings}
        assert new_name in names
        # clean up
        await asyncio.to_thread(store2.conn.delete_container, new_name)
        store2.close()
