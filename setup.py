# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='rtyaml',
    version='0.0.2',
    author=u'Joshua Tauberer',
    author_email=u'jt@occams.info',
    packages=['rtyaml'],
    url='https://github.com/unitedstates/rtyaml',
    license='CC0 (copyright waived)',
    description='All the annoying things to make YAML usable in a source controlled environment.',
    long_description=open("README.rst").read(),
    install_requires=["pyyaml"],
)
