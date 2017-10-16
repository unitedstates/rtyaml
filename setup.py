# -*- coding: utf-8 -*-

# pip3 install twine
# rm -rf dist && python3 setup.py bdist_wheel --universal
# twine upload dist/*
# git tag v1.0.XXX
# git push --tags

from setuptools import setup

setup(
    name='rtyaml',
    version='0.0.4',
    author=u'Joshua Tauberer',
    author_email=u'jt@occams.info',
    packages=['rtyaml'],
    url='https://github.com/unitedstates/rtyaml',
    license='CC0 (copyright waived)',
    description='All the annoying things to make YAML usable in a source controlled environment.',
    long_description=open("README.rst").read(),
    install_requires=["pyyaml"],
)
