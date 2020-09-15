# -*- coding: utf-8 -*-

"""
SwiftStore provides Openstack Swift Object Storage backend for zarr

This class is developed using zarr.ABSStore as reference
(https://github.com/zarr-developers/zarr-python)
"""


from collections.abc import MutableMapping

from swiftclient import Connection
from swiftclient.exceptions import ClientException
from zarr.util import normalize_storage_path
from numcodecs.compat import ensure_bytes


class SwiftStore(MutableMapping):
    """Storage class using Openstack Swift Object Store.

    Parameters
    ----------
    container: string
        swift container to use. It is created if it does not already exists
    prefix: string
        sub-directory path with in the container to store data
    storage_options: dict
        authentication information to connect to the swift store.

    Examples
    --------

    >>> import os
    >>> from zarrswift import SwiftStore
    >>> getenv = os.environ.get
    >>> options = {'preauthurl': getenv('OS_STORAGE_URL'),
    ...            'preauthtoken': getenv('OS_AUTH_TOKEN')}
    >>> store = SwiftStore(container="demo", prefix="zarr_demo", storage_options=options)
    >>> root = zarr.group(store=store, overwrite=True)
    >>> z = root.zeros('foo/bar', shape=(10, 10), chunks=(5, 5), dtype='i4')
    >>> z[:] = 42
    """

    def __init__(self, container, prefix="", storage_options=None):
        self.container = container
        self.prefix = normalize_storage_path(prefix)
        self.storage_options = storage_options or {}
        self.conn = Connection(**self.storage_options)
        self._ensure_container()

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['conn']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.conn = Connection(**self.storage_options)

    def __getitem__(self, name):
        name = self._add_prefix(name)
        try:
            resp, content = self.conn.get_object(self.container, name)
        except ClientException:
            raise KeyError('Object {} not found'.format(name))
        return content

    def __setitem__(self, name, value):
        name = self._add_prefix(name)
        value = ensure_bytes(value)
        self.conn.put_object(self.container, name, value)

    def __delitem__(self, name):
        name = self._add_prefix(name)
        try:
            self.conn.delete_object(self.container, name)
        except ClientException:
            raise KeyError('Object {} not found'.format(name))

    def __eq__(self, other):
        return (
            isinstance(other, SwiftStore)
            and self.container == other.container
            and self.prefix == other.prefix
        )

    def __contains__(self, name):
        return name in self.keys()

    def __iter__(self):
        contents = self._list_container(strip_prefix=True)
        for entry in contents:
            yield entry['name']

    def __len__(self):
        return len(self.keys())

    def _ensure_container(self):
        _, contents = self.conn.get_account()
        listings = [item["name"] for item in contents]
        if self.container not in listings:
            self.conn.put_container(self.container)

    def _add_prefix(self, path):
        path = normalize_storage_path(path)
        path = "/".join([self.prefix, path])
        return normalize_storage_path(path)

    def _list_container(self, path=None, delimiter=None, strip_prefix=False,
                        treat_path_as_dir=True):
        path = self.prefix if path is None else self._add_prefix(path)
        if path and treat_path_as_dir:
            path += '/'
        _, contents = self.conn.get_container(
            self.container, prefix=path, delimiter=delimiter)
        if strip_prefix:
            prefix_size = len(path)
            for entry in contents:
                if 'name' in entry:
                    name = entry['name'][prefix_size:]
                    entry['name'] = normalize_storage_path(name)
                if 'subdir' in entry:
                    name = entry['subdir'][prefix_size:]
                    entry['name'] = normalize_storage_path(name)
                    entry['bytes'] = 0
        return contents

    def keys(self):
        return list(self.__iter__())

    def listdir(self, path=None):
        contents = self._list_container(path, delimiter='/', strip_prefix=True)
        listings = [entry["name"] for entry in contents]
        return sorted(listings)

    def getsize(self, path=None):
        contents = self._list_container(path, strip_prefix=True, treat_path_as_dir=False)
        contents = [entry for entry in contents if '/' not in entry['name']]
        return sum([entry['bytes'] for entry in contents])

    def rmdir(self, path=None):
        contents = self._list_container(path)
        for entry in contents:
            self.conn.delete_object(self.container, entry['name'])

    def clear(self):
        self.rmdir()
