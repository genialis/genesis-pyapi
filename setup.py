#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages


NAME = "GenAPI"
VERSION = "0.1.0"

DESCRIPTION = "A Python API for the Genesis platform."
LONG_DESCRIPTION = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
AUTHOR = "Genialis d.o.o."
AUTHOR_EMAIL = "dev-team@genialis.com"
URL = "https://github.com/genialis/genesis-genapi/"
LICENSE = "Proprietary software"

if __name__ == '__main__':
    setup(
        name = NAME,
        version = VERSION,
        description = DESCRIPTION,
        long_description = LONG_DESCRIPTION,
        author = AUTHOR,
        author_email = AUTHOR_EMAIL,
        url = URL,
        license = LICENSE,
        packages = ['genapi', 'genapi.tests'],
        package_data = {},
        classifiers = [
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: Other/Proprietary License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
        ],
        include_package_data = True,
        zip_safe = False,
        install_requires = [r for r in open('requirements.txt').read().split("\n") if r != "" and r[:2] != "-e"],
        test_suite = 'genapi.tests',
    )
