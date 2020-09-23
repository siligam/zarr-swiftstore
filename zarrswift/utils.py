# -*- coding: utf-8 -*-

import os
import requests


def getenv_auth():
    "Swift auth (v1.0) info from environment variables"
    getenv = os.environ.get
    auth = {
        "preauthurl": getenv("OS_STORAGE_URL"),
        "preauthtoken": getenv("OS_AUTH_TOKEN"),
        "authurl": getenv("ST_AUTH"),
        "user": getenv("ST_USER"),
        "key": getenv("ST_KEY"),
    }
    auth = {k: v for (k, v) in auth.items() if v}
    if not auth:
        raise ValueError("No environment variables found.")
    return auth


def acquire_token(authurl, user, key=None, update_env=True):
    "Swift auth v1.0"
    assert ':' in user, "Must be of the form '<project>:<user>'"
    if not key:
        import getpass
        key = getpass.getpass('Key: ')
    headers = {"X-Auth-User": user, "X-Auth-Key": key}
    r = requests.get(authurl, headers=headers)
    r.raise_for_status()
    token_expires = r.headers.get('x-auth-token-expires')
    if token_expires:
        from datetime import timedelta
        dt = timedelta(seconds=int(token_expires))
        print("Token expires in: " + str(dt))
    auth = {
        "preauthurl": r.headers['x-storage-url'],
        "preauthtoken": r.headers['x-auth-token'],
    }
    if update_env:
        os.environ['OS_STORAGE_URL'] = auth['preauthurl']
        os.environ['OS_AUTH_TOKEN'] = auth['preauthtoken']
    return auth


def is_public(store):
    "check container public read_acl settings"
    acl = store.conn.head_container(store.container).get('x-container-read', '')
    return '.r:*' in acl


def toggle_public(store):
    "toggle container public read_acl settings"
    acl = store.conn.head_container(store.container).get('x-container-read', '')
    if '.r:*' in acl:
        acl = acl.replace('.r:*', '')
    else:
        acl = ",".join([acl, ".r:*,.rlistings"])
    acl = ','.join(sorted(filter(None, set(acl.split(',')))))
    store.conn.post_container(store.container, headers={'X-Container-Read': acl})
