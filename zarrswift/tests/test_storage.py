# -*- coding: utf-8 -*-

import unittest
import pytest
import os

from .. import SwiftStore, AuthMissingParameter

from zarr.tests.test_storage import StoreTests
from zarr.tests.util import CountingDict, skip_test_env_var


def list_containers(conn):
    _, contents = conn.get_account()
    containers = [entry["name"] for entry in contents]
    return containers


@skip_test_env_var("ZARR_TEST_SWIFT")
class TestSwiftStore(StoreTests, unittest.TestCase):
    def create_store(self, prefix=None):
        store = SwiftStore(container="test_swiftstore", prefix=prefix)
        store.rmdir()
        return store

    @pytest.mark.skip(reason="No way to get hierarchy through getsize")
    def test_hierarchy(self):
        # Skip hierarchy test as SwiftStore does not support it via getsize
        pass

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

    def test_ensure_container(self):
        store = self.create_store()
        assert store.container in list_containers(store.conn)
        store.container = "test_ensure_container"
        assert store.container not in list_containers(store.conn)
        store._ensure_container()
        assert store.container in list_containers(store.conn)
        store.conn.delete_container(store.container)
        assert store.container not in list_containers(store.conn)

    def test_listdir(self):
        store = self.create_store(prefix="foo6")
        store["a"] = b"aaaa"
        assert "a" in store.listdir()
        assert "foo6/a" in store.listdir(with_prefix=True)

    def test_authmissingparameter(self):
        names = "ST_AUTH ST_USER ST_KEY OS_STORAGE_URL OS_AUTH_TOKEN".split()
        env = {name: os.environ.pop(name) for name in names if name in os.environ}
        with pytest.raises(AuthMissingParameter):
            store = self.create_store()
        for name, val in env.items():
            os.environ[name] = val

    def test_token_authentication(self):
        "using preauthurl and preauthtoken to create store"
        store1 = self.create_store()
        storageurl = store1.conn.url
        token = store1.conn.token
        store2 = SwiftStore(
            container=store1.container, preauthurl=storageurl, preauthtoken=token
        )
        assert store1 == store2
