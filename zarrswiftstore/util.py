# -*- coding: utf-8 -*-

import os
import getpass
import requests


def new_token(auth_url: str, account: str, user: str, valid_until=86400):
    """Get a token from authentication server.

    valid_until: (seconds)
        Lifetime of storage-url and token (default is 24 hours)
    """
    password = getpass.getpass()
    headers = {
        'X-Auth-User': f'{account}:{user}',
        'X-Auth-Key': f'{password}',
        'X-Auth-Lifetime': str(valid_until),
    }
    r = requests.get(auth_url, headers=headers)
    r.raise_for_status()
    os.environ['OS_STORAGE_URL'] = r.headers['x-storage-url']
    os.environ['OS_AUTH_TOKEN'] = r.headers['x-auth-token']
    
