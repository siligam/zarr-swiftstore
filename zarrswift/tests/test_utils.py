# -*- coding: utf-8 -*-

import os
import pytest
import mock
from .. import SwiftStore
from .. import utils


def test_getenv_auth():
    env_names = ("OS_STORAGE_URL", "OS_AUTH_TOKEN", "ST_AUTH", "ST_USER", "ST_KEY")
    names = ("preauthurl", "preauthtoken", "authurl", "user", "key")

    auth = {name: os.environ.pop(name) for name in env_names if name in os.environ}
    with pytest.raises(ValueError):
        _auth = utils.getenv_auth()

    d = dict.fromkeys(env_names, '')
    os.environ.update(d)
    with pytest.raises(ValueError):
        _auth = utils.getenv_auth()
    for name in d:
        os.environ.pop(name)

    d = dict.fromkeys(env_names[:2], "test")
    os.environ.update(d)
    _auth = utils.getenv_auth()
    for name in names[:2]:
        assert name in _auth
    for name in names[2:]:
        assert name not in _auth
    for name in d:
        os.environ.pop(name)

    d = dict.fromkeys(env_names[2:], "test")
    os.environ.update(d)
    _auth = utils.getenv_auth()
    for name in names[2:]:
        assert name in _auth
    for name in names[:2]:
        assert name not in _auth
    for name in d:
        os.environ.pop(name)

    os.environ.update(auth)


def test_acquire_token():
    
    authurl = os.environ.get('ST_AUTH')
    user = os.environ.get('ST_USER')
    key = os.environ.get('ST_KEY')

    env_names = ("OS_STORAGE_URL", "OS_AUTH_TOKEN")
    names = ("preauthurl", "preauthtoken")

    ref = {name: os.environ.pop(name) for name in env_names if name in os.environ}

    auth = utils.acquire_token(authurl, user, key, update_env=False)
    assert set(auth) == set(names)
    for name in env_names:
        assert os.environ.get(name) is None

    auth = utils.acquire_token(authurl, user, key, update_env=True)
    assert set(auth) == set(names)
    for name in env_names:
        assert os.environ.pop(name) is not None

    os.environ.update(ref)

    with pytest.raises(AssertionError):
        utils.acquire_token(authurl, 'someuser', 'invalid_key', update_env=False)

    import getpass
    with mock.patch('getpass.getpass', return_value=key):
        utils.acquire_token(authurl, user, update_env=False)


def test_is_public():
    auth = {
        "authurl": os.environ.get('ST_AUTH'),
        "user": os.environ.get('ST_USER'),
        "key": os.environ.get('ST_KEY'),
    }
    store = SwiftStore("test_swiftstore", "demo", auth)
    headers = store.conn.head_container(store.container)
    acl = headers.get('x-container-read', '')
    _acl = acl.replace('.r:*', '')
    headers = {'X-Container-Read': _acl}
    store.conn.post_container(store.container, headers=headers)
    assert not utils.is_public(store)

    _acl += ',.r:*'
    headers = {'X-Container-Read': _acl}
    store.conn.post_container(store.container, headers=headers)
    assert utils.is_public(store)

    headers = {'X-Container-Read': acl}
    store.conn.post_container(store.container, headers=headers)


def test_toggle_public():
    auth = {
        "authurl": os.environ.get('ST_AUTH'),
        "user": os.environ.get('ST_USER'),
        "key": os.environ.get('ST_KEY'),
    }
    store = SwiftStore("test_swiftstore", "demo", auth)
    container = store.container
    headers = store.conn.head_container(container)
    acl = headers.get('x-container-read', '')

    _acl = acl.replace('.r:*', '')
    headers = {'X-Container-Read': _acl}
    store.conn.post_container(container, headers=headers)

    utils.toggle_public(store)
    _acl = store.conn.head_container(container).get('x-container-read', '')
    assert '.r:*' in _acl

    utils.toggle_public(store)
    _acl = store.conn.head_container(container).get('x-container-read', '')
    assert '.r:*' not in _acl
