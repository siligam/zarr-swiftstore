"""
SwiftStore: OpenStack Swift Object Storage backend for zarr v3.

The store wraps python-swiftclient's synchronous Connection API with
asyncio.to_thread so that Swift I/O never blocks the event loop.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from swiftclient import Connection
from swiftclient.exceptions import ClientException

from zarr.abc.store import (
    OffsetByteRequest,
    RangeByteRequest,
    Store,
    SuffixByteRequest,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable

    from zarr.abc.store import ByteRequest
    from zarr.core.buffer import Buffer, BufferPrototype


class SwiftStore(Store):
    """zarr v3 storage backend for OpenStack Swift Object Storage.

    Parameters
    ----------
    container:
        Swift container name. Created on ``open()`` if it does not exist.
    prefix:
        Optional path prefix inside the container.
    storage_options:
        Keyword arguments forwarded to ``swiftclient.Connection`` (e.g.
        ``preauthurl``, ``preauthtoken``, ``authurl``, ``user``, ``key``).
    read_only:
        Open the store in read-only mode.

    Examples
    --------
    >>> import os, zarr
    >>> from zarrswift import SwiftStore
    >>> store = await SwiftStore.open(
    ...     container="demo",
    ...     prefix="zarr_demo",
    ...     storage_options={
    ...         "preauthurl": os.environ["OS_STORAGE_URL"],
    ...         "preauthtoken": os.environ["OS_AUTH_TOKEN"],
    ...     },
    ... )
    >>> root = zarr.open_group(store=store, mode="w")
    """

    supports_writes: bool = True
    supports_deletes: bool = True
    supports_listing: bool = True

    def __init__(
        self,
        container: str,
        prefix: str = "",
        storage_options: dict[str, Any] | None = None,
        *,
        read_only: bool = False,
    ) -> None:
        super().__init__(read_only=read_only)
        self.container = container
        self.prefix = prefix.strip("/")
        self.storage_options = storage_options or {}
        self.conn = Connection(**self.storage_options)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _open(self) -> None:
        await self._ensure_container()
        await super()._open()

    def with_read_only(self, read_only: bool = False) -> SwiftStore:
        return type(self)(
            self.container,
            prefix=self.prefix,
            storage_options=self.storage_options,
            read_only=read_only,
        )

    # ------------------------------------------------------------------
    # Pickle support (Connection is not picklable)
    # ------------------------------------------------------------------

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        del state["conn"]
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        self.conn = Connection(**self.storage_options)

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"SwiftStore(container={self.container!r}, prefix={self.prefix!r})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, SwiftStore)
            and self.container == other.container
            and self.prefix == other.prefix
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _full_key(self, key: str) -> str:
        """Build the full Swift object name from a store-relative key."""
        if not self.prefix:
            return key
        return f"{self.prefix}/{key}" if key else f"{self.prefix}/"

    def _strip_prefix(self, full_key: str) -> str:
        """Remove the store prefix from a full Swift object name."""
        if self.prefix:
            drop = len(self.prefix) + 1  # prefix + "/"
            return full_key[drop:]
        return full_key

    async def _ensure_container(self) -> None:
        """Create the Swift container if it does not already exist."""
        def _check_or_create() -> None:
            _, listings = self.conn.get_account()
            names = {item["name"] for item in listings}
            if self.container not in names:
                self.conn.put_container(self.container)

        await asyncio.to_thread(_check_or_create)

    @staticmethod
    def _range_header(byte_range: ByteRequest) -> str:
        if isinstance(byte_range, RangeByteRequest):
            return f"bytes={byte_range.start}-{byte_range.end - 1}"
        if isinstance(byte_range, OffsetByteRequest):
            return f"bytes={byte_range.offset}-"
        if isinstance(byte_range, SuffixByteRequest):
            return f"bytes=-{byte_range.suffix}"
        raise ValueError(f"Unexpected byte_range, got {byte_range}.")

    # ------------------------------------------------------------------
    # Core async store interface
    # ------------------------------------------------------------------

    async def get(
        self,
        key: str,
        prototype: BufferPrototype,
        byte_range: ByteRequest | None = None,
    ) -> Buffer | None:
        full_key = self._full_key(key)
        if byte_range is not None and not isinstance(
            byte_range, (RangeByteRequest, OffsetByteRequest, SuffixByteRequest)
        ):
            raise ValueError(f"Unexpected byte_range, got {byte_range}.")

        headers = {"Range": self._range_header(byte_range)} if byte_range is not None else {}

        def _fetch() -> bytes:
            _, content = self.conn.get_object(
                self.container, full_key, headers=headers or None
            )
            return content

        try:
            content = await asyncio.to_thread(_fetch)
        except ClientException:
            return None
        return prototype.buffer.from_bytes(content)

    async def get_partial_values(
        self,
        prototype: BufferPrototype,
        key_ranges: Iterable[tuple[str, ByteRequest | None]],
    ) -> list[Buffer | None]:
        return list(
            await asyncio.gather(
                *(self.get(key, prototype, byte_range) for key, byte_range in key_ranges)
            )
        )

    async def exists(self, key: str) -> bool:
        full_key = self._full_key(key)
        try:
            await asyncio.to_thread(self.conn.head_object, self.container, full_key)
            return True
        except ClientException:
            return False

    async def set(self, key: str, value: Buffer) -> None:
        self._check_writable()
        full_key = self._full_key(key)
        data = value.to_bytes()
        await asyncio.to_thread(self.conn.put_object, self.container, full_key, data)

    async def delete(self, key: str) -> None:
        self._check_writable()
        full_key = self._full_key(key)
        try:
            await asyncio.to_thread(self.conn.delete_object, self.container, full_key)
        except ClientException:
            pass  # idempotent — key may not exist

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    async def list(self) -> AsyncIterator[str]:
        async for key in self.list_prefix(""):
            yield key

    async def list_prefix(self, prefix: str) -> AsyncIterator[str]:
        full_prefix = self._full_key(prefix)
        _, contents = await asyncio.to_thread(
            self.conn.get_container, self.container, prefix=full_prefix
        )
        for entry in contents:
            name = entry.get("name", "")
            if name:
                yield self._strip_prefix(name)

    async def list_dir(self, prefix: str) -> AsyncIterator[str]:
        if prefix:
            full_prefix = self._full_key(prefix.rstrip("/")) + "/"
        elif self.prefix:
            full_prefix = f"{self.prefix}/"
        else:
            full_prefix = ""

        _, contents = await asyncio.to_thread(
            self.conn.get_container,
            self.container,
            prefix=full_prefix,
            delimiter="/",
        )
        for entry in contents:
            # "name" → actual object at this level
            # "subdir" → virtual directory
            name = entry.get("name") or entry.get("subdir", "")
            if not name:
                continue
            relative = name[len(full_prefix):].rstrip("/")
            if relative:
                yield relative

    # ------------------------------------------------------------------
    # Efficient size queries using Swift HEAD
    # ------------------------------------------------------------------

    async def getsize(self, key: str) -> int:
        full_key = self._full_key(key)
        try:
            headers = await asyncio.to_thread(
                self.conn.head_object, self.container, full_key
            )
            return int(headers.get("content-length", 0))
        except ClientException:
            raise FileNotFoundError(key)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def url(self) -> str:
        """Public URL of the store root."""
        parts = [self.conn.url, self.container]
        if self.prefix:
            parts.append(self.prefix)
        return "/".join(parts)
