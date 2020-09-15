# -*- coding: utf-8 -*-

import unittest
import pytest
import os

from .. import SwiftStore

from zarr.tests.test_storage import StoreTests
from zarr.tests.util import skip_test_env_var


def list_containers(conn):
    _, contents = conn.get_account()
    containers = [entry["name"] for entry in contents]
    return containers


@skip_test_env_var("ZARR_TEST_SWIFT")
class TestSwiftStore(StoreTests, unittest.TestCase):
    def create_store(self, prefix=None):
        getenv = os.environ.get
        options = {
            "preauthurl": getenv("OS_STORAGE_URL"),
            "preauthtoken": getenv("OS_AUTH_TOKEN"),
            "authurl": getenv("ST_AUTH"),
            "user": getenv("ST_USER"),
            "key": getenv("ST_KEY"),
        }
        store = SwiftStore(
            container="test_swiftstore", prefix=prefix, storage_options=options
        )
        store.clear()
        return store

    def test_iterators_with_prefix(self):
        for prefix in [
            "test_prefix",
            "/test_prefix",
            "test_prefix/",
            "test/prefix",
            "",
            None,
        ]:
            store = self.create_store(prefix=prefix)

            # test iterator methods on empty store
            assert 0 == len(store)
            assert set() == set(store)
            assert set() == set(store.keys())
            assert set() == set(store.values())
            assert set() == set(store.items())

            # setup some values
            store["a"] = b"aaa"
            store["b"] = b"bbb"
            store["c/d"] = b"ddd"
            store["c/e/f"] = b"fff"

            # test iterators on store with data
            assert 4 == len(store)
            assert {"a", "b", "c/d", "c/e/f"} == set(store)
            assert {"a", "b", "c/d", "c/e/f"} == set(store.keys())
            assert {b"aaa", b"bbb", b"ddd", b"fff"} == set(store.values())
            assert {
                ("a", b"aaa"),
                ("b", b"bbb"),
                ("c/d", b"ddd"),
                ("c/e/f", b"fff"),
            } == set(store.items())

    def test_equal(self):
        store1 = self.create_store()
        store2 = self.create_store()
        assert store1 == store2

    def test_ensure_container(self):
        store = self.create_store()
        assert store.container in list_containers(store.conn)
        store.container = "test_ensure_container"
        assert store.container not in list_containers(store.conn)
        store._ensure_container()
        assert store.container in list_containers(store.conn)
        store.conn.delete_container(store.container)
        assert store.container not in list_containers(store.conn)
