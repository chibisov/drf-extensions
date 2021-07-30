## Django REST Framework extensions

DRF-extensions is a collection of custom extensions for [Django REST Framework](https://github.com/tomchristie/django-rest-framework)

Full documentation for project is available at [http://chibisov.github.io/drf-extensions/docs](http://chibisov.github.io/drf-extensions/docs)

[![Build Status](https://travis-ci.org/chibisov/drf-extensions.svg?branch=master)](https://travis-ci.org/chibisov/drf-extensions)
[![Backers on Open Collective](https://opencollective.com/drf-extensions/backers/badge.svg)](#backers) [![Sponsors on Open Collective](https://opencollective.com/drf-extensions/sponsors/badge.svg)](#sponsors) [![PyPI](https://img.shields.io/pypi/v/drf-extensions.svg)](https://pypi.python.org/pypi/drf-extensions)

### Sponsor

[Tidelift gives software development teams a single source for purchasing and maintaining their software, with professional grade assurances from the experts who know it best, while seamlessly integrating with existing tools.](https://tidelift.com/subscription/pkg/pypi-drf-extensions?utm_source=pypi-drf-extensions&utm_medium=referral&utm_campaign=readme)


## Requirements

* Tested for Python 3.6, 3.7 and 3.8
* Tested for Django Rest Framework 3.12
* Tested for Django 2.2 to 3.2
* Tested for django-filter 2.1.0

## Installation:

    pip3 install drf-extensions
    
    or from github
    
    pip3 install https://github.com/chibisov/drf-extensions/archive/master.zip

## Some features

* DetailSerializerMixin
* Caching
* Conditional requests
* Customizable key construction for caching and conditional requests
* Nested routes
* Bulk operations

Read more in [documentation](http://chibisov.github.io/drf-extensions/docs)

## Development

Running the tests:

    $ pip3 install tox
    $ tox -- tests_app

Running test for exact environment:

    $ tox -e py38 -- tests_app

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

Automatically build docs by watching changes:

    $ pip install watchdog
    $ make watch_docs

## Developing new features

Every new feature should be:

* Documented
* Tested
* Implemented
* Pushed to main repository

### How to write documentation

When new feature implementation starts you should place it into `development version` pull. Add `Development version`
section to `Release notes` and describe every new feature in it. Use `#anchors` to facilitate navigation.

Every feature should have title and information that it was implemented in current development version.

For example if we've just implemented `Usage of the specific cache`:

    ...

    #### Usage of the specific cache

    *New in DRF-extensions development version*

    `@cache_response` can also take...

    ...

    ### Release notes

    ...

    #### Development version

    * Added ability to [use a specific cache](#usage-of-the-specific-cache) for `@cache_response` decorator

## Publishing new releases

Increment version in `rest_framework_extensions/__init__.py`. For example:

    __version__ = '0.2.2'  # from 0.2.1

Move to new version section all release notes in documentation.

Add date for release note section.

Replace in documentation all `New in DRF-extensions development version` notes to `New in DRF-extensions 0.2.2`.

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

## Contributors

This project exists thanks to all the people who contribute. <img src="https://opencollective.com/drf-extensions/contributors.svg?width=890&button=false" />


## Backers

Thank you to all our backers! 🙏 [[Become a backer](https://opencollective.com/drf-extensions#backer)]

<a href="https://opencollective.com/drf-extensions#backers" target="_blank"><img src="https://opencollective.com/drf-extensions/backers.svg?width=890"></a>


## Sponsors

Support this project by becoming a sponsor. Your logo will show up here with a link to your website. [[Become a sponsor](https://opencollective.com/drf-extensions#sponsor)]

<a href="https://opencollective.com/drf-extensions/sponsor/0/website" target="_blank"><img src="https://opencollective.com/drf-extensions/sponsor/0/avatar.svg"></a>
<a href="https://opencollective.com/drf-extensions/sponsor/1/website" target="_blank"><img src="https://opencollective.com/drf-extensions/sponsor/1/avatar.svg"></a>
<a href="https://opencollective.com/drf-extensions/sponsor/2/website" target="_blank"><img src="https://opencollective.com/drf-extensions/sponsor/2/avatar.svg"></a>
<a href="https://opencollective.com/drf-extensions/sponsor/3/website" target="_blank"><img src="https://opencollective.com/drf-extensions/sponsor/3/avatar.svg"></a>
<a href="https://opencollective.com/drf-extensions/sponsor/4/website" target="_blank"><img src="https://opencollective.com/drf-extensions/sponsor/4/avatar.svg"></a>
<a href="https://opencollective.com/drf-extensions/sponsor/5/website" target="_blank"><img src="https://opencollective.com/drf-extensions/sponsor/5/avatar.svg"></a>
<a href="https://opencollective.com/drf-extensions/sponsor/6/website" target="_blank"><img src="https://opencollective.com/drf-extensions/sponsor/6/avatar.svg"></a>
<a href="https://opencollective.com/drf-extensions/sponsor/7/website" target="_blank"><img src="https://opencollective.com/drf-extensions/sponsor/7/avatar.svg"></a>
<a href="https://opencollective.com/drf-extensions/sponsor/8/website" target="_blank"><img src="https://opencollective.com/drf-extensions/sponsor/8/avatar.svg"></a>
<a href="https://opencollective.com/drf-extensions/sponsor/9/website" target="_blank"><img src="https://opencollective.com/drf-extensions/sponsor/9/avatar.svg"></a>


