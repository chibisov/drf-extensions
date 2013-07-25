#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
import re
import os


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.match("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


version = get_version('rest_framework_extensions')


setup(
    name='drf-extensions',
    version=version,
    url='http://github.com/chibisov/drf-extensions',
    # download_url='http://pypi.python.org/pypi/rest_framework_extensions/',  # todo
    license='BSD',
    install_requires=['djangorestframework>=2.3.5'],
    description='Extensions for Django REST Framework',
    long_description='DRF-extensions is a collection of custom extensions for Django REST Framework',
    author='Gennady Chibisov',
    author_email='web-chib@ya.ru',
    packages=get_packages('rest_framework_extensions'),
    package_data=get_package_data('rest_framework_extensions'),
    test_suite='rest_framework_extensions.runtests.runtests.main',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
    ]
)