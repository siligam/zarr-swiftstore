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

    def test_walk(self):
        store = self.create_store(prefix="foo6")
        store["a"] = b"aaaa"
        assert "a" in store._walk()
        assert "foo6/a" in store._walk(with_prefix=True)

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

    def test_hierarchy(self):
        # setup
        store = self.create_store()
        store['a'] = b'aaa'
        store['b'] = b'bbb'
        store['c/d'] = b'ddd'
        store['c/e/f'] = b'fff'
        store['c/e/g'] = b'ggg'

        # check keys
        assert 'a' in store
        assert 'b' in store
        assert 'c/d' in store
        assert 'c/e/f' in store
        assert 'c/e/g' in store
        assert 'c' not in store
        assert 'c/' not in store
        assert 'c/e' not in store
        assert 'c/e/' not in store
        assert 'c/d/x' not in store

        # check __getitem__
        with pytest.raises(KeyError):
            store['c']
        with pytest.raises(KeyError):
            store['c/e']
        with pytest.raises(KeyError):
            store['c/d/x']

        # test getsize (optional)
        if hasattr(store, 'getsize'):
            # assert 6 == store.getsize()  # how is this 6? (5 * 3 bytes)
            assert 15 == store.getsize()
            assert 3 == store.getsize('a')
            assert 3 == store.getsize('b')
            # assert 3 == store.getsize('c')  # how is this 3? (3 * 3bytes)
            assert 9 == store.getsize('c')
            assert 3 == store.getsize('c/d')
            assert 6 == store.getsize('c/e')
            assert 3 == store.getsize('c/e/f')
            assert 3 == store.getsize('c/e/g')
            # non-existent paths
            assert 0 == store.getsize('x')
            assert 0 == store.getsize('a/x')
            assert 0 == store.getsize('c/x')
            assert 0 == store.getsize('c/x/y')
            assert 0 == store.getsize('c/d/y')
            assert 0 == store.getsize('c/d/y/z')

        # test listdir (optional)
        if hasattr(store, 'listdir'):
            assert {'a', 'b', 'c'} == set(store.listdir())
            assert {'d', 'e'} == set(store.listdir('c'))
            assert {'f', 'g'} == set(store.listdir('c/e'))
            # no exception raised if path does not exist or is leaf
            assert [] == store.listdir('x')
            assert [] == store.listdir('a/x')
            assert [] == store.listdir('c/x')
            assert [] == store.listdir('c/x/y')
            assert [] == store.listdir('c/d/y')
            assert [] == store.listdir('c/d/y/z')
            assert [] == store.listdir('c/e/f')

        # test rmdir (optional)
        if hasattr(store, 'rmdir'):
            store.rmdir('c/e')
            assert 'c/d' in store
            assert 'c/e/f' not in store
            assert 'c/e/g' not in store
            store.rmdir('c')
            assert 'c/d' not in store
            store.rmdir()
            assert 'a' not in store
            assert 'b' not in store
            store['a'] = b'aaa'
            store['c/d'] = b'ddd'
            store['c/e/f'] = b'fff'
            # no exceptions raised if path does not exist or is leaf
            store.rmdir('x')
            store.rmdir('a/x')
            store.rmdir('c/x')
            store.rmdir('c/x/y')
            store.rmdir('c/d/y')
            store.rmdir('c/d/y/z')
            store.rmdir('c/e/f')
            assert 'a' in store
            assert 'c/d' in store
            # assert 'c/e/f' in store  # this is false statement. removed earlier
            assert 'c/e/f' not in store
