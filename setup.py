# -*- coding: utf-8 -*-

# python3 -m pip install --user --upgrade setuptools wheel twine
# rm -rf dist && python3 setup.py sdist bdist_wheel --universal
# twine upload dist/*
# git tag v1.0.XXX
# git push --tags

from setuptools import setup

setup(
    name='rtyaml',
    version='1.0.0',
    author=u'Joshua Tauberer',
    author_email=u'jt@occams.info',
    packages=['rtyaml'],
    url='https://github.com/unitedstates/rtyaml',
    license='CC0 (copyright waived)',
    description='All the annoying things to make YAML usable in a source controlled environment.',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=["pyyaml"],
)
