## Django REST Framework extensions

DRF-extensions is a collection of custom extensions for [Django REST Framework](https://github.com/tomchristie/django-rest-framework)

Full documentation for project is available at [http://chibisov.github.io/drf-extensions/docs](http://chibisov.github.io/drf-extensions/docs)

[![Build Status](https://travis-ci.org/chibisov/drf-extensions.png?branch=master)](https://travis-ci.org/chibisov/drf-extensions)

## Installation:

    pip install drf-extensions

## Extensions

* Collection level `@action` and `@link` decorators
* DetailSerializerMixin
* Response pluggable caching

## Development

Run tests:

    $ python setup.py test

Build docs:

    $ cd docs
    $ python backdoc.py --source index.md --title "Django Rest Framework extensions documentation" > index.html