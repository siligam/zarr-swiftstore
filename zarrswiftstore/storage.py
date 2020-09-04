# -*- coding: utf-8 -*-

"""
SwfitStore provides a storage back-end for zarr

This class is modeled after ABSStore (zarr.store.ABSStore)
"""

import os
from collections.abc import MutableMapping
from zarr.util import normalize_storage_path
from swiftclient.client import Connection
# from numcodecs.compact import ensure_bytes


class SwiftStore(MutableMapping):
    """Storage class using openstack swift object store
    
    Parameters
    ----------
    container: string
        The name of the swift object container
    prefix: string
        sub-directory path with in the container to store data
    storageurl: string
        openstack swift object storege url
    token: string
        pre-authenticated token to aceess object storage 
    """
    def __init__(self, container, prefix='', storageurl=None, token=None):
        self.container = container
        self.prefix = normalize_storage_path(prefix)
        storageurl = storageurl or os.environ.get('OS_STORAGE_URL')
        token = token or os.environ.get('OS_AUTH_TOKEN')
        if (storageurl is None) or (token is None):
            raise ValueError('Missing storageurl/token')
        self.client = Connection(preauthurl=storageurl, preauthtoken=token)
        self._ensure_container()
        
    def _ensure_container(self):
        _, contents = self.client.get_account()
        listings = [item['name'] for item in contents]
        if self.container not in listings:
            self.client.put_container(self.container)

    def _add_prefix(self, path):
        path = '/'.join([self.prefix, path])
        return normalize_storage_path(path)
    
    def __getitem__(self, name):
        name = self._add_prefix(name)
        resp, content = self.client.get_object(self.container, name)
        return content
    
    def __setitem__(self, name, value):
        name = self._add_prefix(name)
        # value = ensure_bytes(value)
        self.client.put_object(self.container, name, value)
    
    def __delitem__(self, name):
        name = self._add_prefix(name)
        self.client.delete_object(self.container, name)

    def __eq__(self, other):
        return (
            isinstance(other, SwiftStore) and
            self.container == other.container and
            self.prefix == other.prefix
        )
        
    def listdir(self, path=None, with_prefix=False):
        if path is None:
            path = self.prefix
        else:
            path = self._add_prefix(path)
        _, contents = self.client.get_container(self.container, prefix=path)
        listings = [entry['name'] for entry in contents]
        if not with_prefix and self.prefix:
            # remove prefix length + trailing slash
            prefix_size = len(self.prefix) + 1
            listings = [entry[prefix_size:] for entry in listings]
        return listings

    def __contains__(self, name):
        return name in self.listdir()

    def __iter__(self):
        for entry in self.listdir():
            yield entry
            
    def keys(self):
        return list(self.__iter__())
    
    def __len__(self):
        return len(self.keys())
    
    def getsize(self, path=None):
        'object(s) size in bytes'
        if path is None:
            path = self.prefix
        else:
            path = self._add_prefix(path)
        _, contents = self.client.get_container(self.container, prefix=path)
        try:
            size = contents['bytes']
        except TypeError:
            size = sum(entry['bytes'] for entry in contents)
        return size
    
    def rmdir(self, path=None):
        for entry in self.listdir(path, with_prefix=True):
            self.client.delete_object(self.container, entry)
        return
    
    def clear(self):
        self.rmdir()
    
