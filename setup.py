#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages


NAME = 'Genesis-PyAPI'
VERSION = '1.2.1'
DESCRIPTION = "Python API for the Genesis platform."
LONG_DESCRIPTION = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
AUTHOR = 'Genialis, Inc.'
AUTHOR_EMAIL = 'dev-team@genialis.com'
URL = 'https://github.com/genialis/genesis-pyapi/'
LICENSE = 'Apache License (2.0)'

if __name__ == '__main__':
    setup(
        name=NAME,
        version=VERSION,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        url=URL,
        license=LICENSE,
        packages=find_packages(),
        package_data={},
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ],
        include_package_data=True,
        zip_safe=False,
        install_requires=(
            "requests>=2.6.0",
            "slumber>=0.7.1",
        ),
        extras_require={
            'docs':  [
                'sphinx>=1.7.0',
            ],
        },
        test_suite='genesis.tests'
    )
