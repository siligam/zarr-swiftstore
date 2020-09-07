import unittest
import pytest

from .. import SwiftStore

from zarr.tests.test_storage import StoreTests
from zarr.tests.util import CountingDict, skip_test_env_var


@skip_test_env_var("ZARR_TEST_SWIFT")
class TestSwiftStore(StoreTests, unittest.TestCase):

    def create_store(self, prefix=None):
        store = SwiftStore(container='test123')
        store.rmdir()
        return store

    @pytest.mark.skip(reason="No way to get hierarchy through getsize")
    def test_hierarchy(self):
        # Skip hierarchy test as SwiftStore does not support it via getsize
        pass

    def test_iterators_with_prefix(self):
        for prefix in ['test_prefix', '/test_prefix', 'test_prefix/', 'test/prefix', '', None]:
            store = self.create_store(prefix=prefix)

            # test iterator methods on empty store
            assert 0 == len(store)
            assert set() == set(store)
            assert set() == set(store.keys())
            assert set() == set(store.values())
            assert set() == set(store.items())

            # setup some values
            store['a'] = b'aaa'
            store['b'] = b'bbb'
            store['c/d'] = b'ddd'
            store['c/e/f'] = b'fff'

            # test iterators on store with data
            assert 4 == len(store)
            assert {'a', 'b', 'c/d', 'c/e/f'} == set(store)
            assert {'a', 'b', 'c/d', 'c/e/f'} == set(store.keys())
            assert {b'aaa', b'bbb', b'ddd', b'fff'} == set(store.values())
            assert ({('a', b'aaa'), ('b', b'bbb'), ('c/d', b'ddd'), ('c/e/f', b'fff')} ==
                    set(store.items()))
