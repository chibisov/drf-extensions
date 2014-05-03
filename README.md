## Django REST Framework extensions

DRF-extensions is a collection of custom extensions for [Django REST Framework](https://github.com/tomchristie/django-rest-framework)

Full documentation for project is available at [http://chibisov.github.io/drf-extensions/docs](http://chibisov.github.io/drf-extensions/docs)

[![Build Status](https://travis-ci.org/chibisov/drf-extensions.png?branch=master)](https://travis-ci.org/chibisov/drf-extensions)

## Requirements

* Tested for python 2.7 and 3.3 versions
* Tested for all releases of Django Rest Framework from 2.3.5 to 2.3.13 versions
* Tested for Django 1.5.5, 1.6.2 and 1.7

## Installation:

    pip install drf-extensions

## Some features

* DetailSerializerMixin
* Collection level `@action` and `@link` controller decorators
* Custom endpoint name for `@action` and `@link` decorators
* Caching
* Conditional requests
* Customizable key construction for caching and conditional requests

Read more in [documentation](http://chibisov.github.io/drf-extensions/docs)

## Development

Running the tests:

    $ pip install tox
    $ tox -- tests_app

Running test for exact environment:

    $ tox -e py27-drf2.3.5 -- tests_app

Recreate envs before running tests:

    $ tox --recreate -- tests_app

Pass custom arguments:

    $ tox -- tests_app --verbosity=3

Run with pdb support:

    $ tox -- tests_app --processes=0 --nocapture

Run exact TestCase:

    $ tox -- tests_app.tests.unit.mixins.tests:DetailSerializerMixinTest_serializer_detail_class

Run tests from exact module:

    $ tox -- tests_app.tests.unit.mixins.tests

Build docs:

    $ make build_docs

## Publishing new releases

Increment version in `rest_framework_extensions/__init__.py`. For example:

    __version__ = '0.2.2'  # from 0.2.1

Move to new version section all release notes in documentation.

Replace in documentation all `New in DRF-extensions development version` notes to `New in DRF-extensions 0.2.2`

Rebuild documentation.

Run tests.

Commit changes with message "Version 0.2.2"

Add new tag version for commit:

    $ git tag 0.2.2

Push to master with tags:

    $ git push origin master --tags

Don't forget to merge `master` to `gh-pages` branch and push to origin:

    $ git co gh-pages
    $ git merge --no-ff master
    $ git push origin gh-pages

Publish to pypi:

    $ python setup.py publish