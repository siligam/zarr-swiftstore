# -*- coding: utf-8 -*-

"""
SwiftStore provides openstack swift object storage backend for zarr

This class is developed using zarr.ABSStore as reference
(https://github.com/zarr-developers/zarr-python)
"""

import os
from collections.abc import MutableMapping

from swiftclient import Connection
import swiftclient.exceptions
from zarr.util import normalize_storage_path

from numcodecs.compat import ensure_bytes


class AuthMissingParameter(KeyError):
    pass


class SwiftStore(MutableMapping):
    """Storage class using openstack swift object store.

    To establish a connection to swift object store, provide (authurl, user, key)
    or (preauthurl, preauthtoken). Another way to provide these values is through
    environment variables (ST_AUTH, ST_USER, ST_KEY) or (OS_STORAGE_URL, OS_AUTH_TOKEN)

    Parameters
    ----------
    container: string
        The name of the swift object container
    prefix: string
        sub-directory path with in the container to store data
    authurl: string
        authentication url
    user: string
        user details of the form "account:user"
    key: string
        key is password
    preauthurl: string
        storage-url
    preauthtoken: string
        pre-authenticated token to aceess object storage
    """

    def __init__(
        self,
        container,
        prefix="",
        authurl=None,
        user=None,
        key=None,
        preauthurl=None,
        preauthtoken=None,
    ):
        self.container = container
        self.prefix = normalize_storage_path(prefix)
        self.conn = self._make_connection(authurl, user, key, preauthurl, preauthtoken)
        self._ensure_container()

    def _make_connection(
        self, authurl=None, user=None, key=None, preauthurl=None, preauthtoken=None
    ):
        "make a connection object either from pre-authenticated token or using authurl"
        getenv = os.environ.get
        authurl = authurl or getenv("ST_AUTH")
        user = user or getenv("ST_USER")
        key = key or getenv("ST_KEY")
        preauthurl = preauthurl or getenv("OS_STORAGE_URL")
        preauthtoken = preauthtoken or getenv("OS_AUTH_TOKEN")
        if preauthurl and preauthtoken:
            conn = Connection(preauthurl=preauthurl, preauthtoken=preauthtoken)
        elif authurl and user and key:
            conn = Connection(authurl, user=user, key=key)
        else:
            raise AuthMissingParameter(
                "Missing required values (authurl, user, key) or (preauthurl, preauthtoken)"
            )
        return conn

    def __getitem__(self, name):
        name = self._add_prefix(name)
        try:
            resp, content = self.conn.get_object(self.container, name)
        except swiftclient.exceptions.ClientException:
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
        except swiftclient.exceptions.ClientException:
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
