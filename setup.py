#!/usr/bin/env python
from distutils.core import setup

kwargs = {
    "name": "emmer",
    "version": "1.0",
    "packages": ["emmer"],
    "description": "Python Client Library for PagerDuty's REST API",
    "author": "David Mah",
    "maintainer": "David Mah",
    "author_email": "MahHaha@gmail.com",
    "maintainer_email": "MahHaha@gmail.com",
    "license": "MIT",
    "url": "https://github.com/dropbox/emmer",
    "download_url": "https://github.com/dropbox/emmer/archive/master.tar.gz",
}

setup(**kwargs)
