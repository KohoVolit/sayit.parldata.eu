-----------------
sayit.parldata.eu
-----------------

This repository contains a Django project that uses the SayIt component
to provide transcripts of parliament debates in Visegrad and Balkan
countries in a modern, searchable format.

SayIt is a `Poplus component <http://poplus.org>`_
by `mySociety <http://www.mysociety.org/>`_.

.. contents:: :backlinks: none


Installation
============

See `installation instructions`_ in a separate document.

.. _`installation instructions`: INSTALL.rst


Adding of a new parliament
==========================

Each parliament is hosted on its own subdomain, e.g.
``nrsr.sk.sayit.parldata.eu`` for National Council of Slovak Republic.

The SayIt component allows multiple subdomain based instances. All of them
are stored in one database and share settings like collation (needed for
language-dependent sorting), timezone or fulltext search configuration.

Because we need to set those settings individually for each parliament,
the multi-instance functionality of SayIt cannot be used and we must
implemented it differently.

A separate WSGI application runs for each parliament initialized with
parliament-specific settings. All WSGI applications share the same
codebase and the same Django project with common settings.

The following steps are needed to add a new parliament:

#. Create a new database with collation settings corresponding to language
of the parliament. Example:

    .. code-block:: SQL
        CREATE DATABASE sayit_sk_nrsr WITH LC_CTYPE 'sk_SK.UTF-8' LC_COLLATE 'sk_SK.UTF-8' TEMPLATE template0 OWNER sayit;

#. Copy one of the subdirectories in ``/subdomains`` directory under a
new name and adjust content of the ``settings.py`` file within. Follow
the naming conventions there. The directory name can contain only letters
and underscore because it represents a python module.

#. Create database tables:

    .. code-block:: console
        $ source /home/projects/.virtualenvs/sayit/bin/activate
        (sayit)$ subdomains/sk_nrsr/manage.py syncdb
        (sayit)$ subdomains/sk_nrsr/manage.py migrate
        (sayit)$ deactivate

#. Modify ``/etc/apache2/sites-available/sayit.parldata.eu.conf``, copy
one of the ``VirtualHost`` blocks and edit the copy to correspond with
the new parliament. Then

    .. code-block:: console
        $ sudo service apache2 reload

#. Create a new Google Analytics property within the existing GA account
and set the two-digit code of the property in the ``settings.py`` file
above.


Importing of data
=================

Data are imported in `AkomaNtoso format (XML)`_ (debates) and
`Popolo format (JSON)`_ (speakers) via commandline script ``manage.py``
of the particular subdomain and special Django commands. The script must
be executed in virtual environment of the installation.

.. code-block:: console
    $ source /home/projects/.virtualenvs/sayit/bin/activate

.. _`AkomaNtoso format (XML)`: http://sayit.mysociety.org/about/developers
.. _`Popolo format (JSON)`: http://www.popoloproject.com/specs/person.html


Examples
--------

To import speakers from a given file to Slovak parliament subdomain use:

.. code-block:: console
    (sayit)$ /home/projects/sayit/subdomains/sk_nrsr/manage.py sayit_load_speakers /home/projects/export-to-sayit/sk/nrsr/people.json

To import debates from all files in a given directory to Slovak parliament
subdomain use:

.. code-block:: console
    (sayit)$ /home/projects/sayit/subdomains/sk_nrsr/manage.py load_akomantoso --dir /home/projects/export-to-sayit/sk --instance default --commit --merge-existing

To delete all data from the Slovak parliament subdomain use:

.. code-block:: console
    (sayit)$ subdomains/sk_nrsr/manage.py flush

Schedule those scripts to be executed by Cron if regular updates are needed.


Some implementation notes
=========================

Web admin interface
-------------------

Administration through web interface is disabled as well as logging in.
Data can be manipulated only by the commands above.


Templates customization
-----------------------

SayIt templates that needed to be modified are duplicated from SayIt to
``sayit_parladata_eu/templates`` directory and adjusted there. Those
templates override the original SayIt ones thanks to installed Django
application `django-apptemplates`_.

.. _`django-apptemplates`: https://pypi.python.org/pypi/django-apptemplates/


CSS customization
-----------------

`SayIt uses`_ SASS, Compass, and Foundation for its CSS. Minor tweaks for
this project are placed into a simple CSS file
``sayit_parladata_eu/static/css/tweaks.css``. Run
``manage.py collectstatic`` after any CSS modification.

.. _`SayIt uses`: http://mysociety.github.io/sayit/develop/


Settings loading
----------------

All instances corresponding to the subdomains share the same codebase and
the same Django project. Each subdomain has its own ``VirtualHost`` block
in Apache config file and its own settings in the ``subdomains``
directory. The settings for a particular subdomain are loaded as follows:

The ``VirtualHost`` block in Apache config file points to the subdomain's
WSGI application file ``subdomains/<subdom>/wsgi.py`` which loads
settings file from the same directory. The settings file imports common
settings from ``sayit_parldata_eu/settings/base.py`` and overrides the
parliament-specific ones. The common settings file loads private settings
from ``conf/private.yml`` that is not present in the repository.

The same mechanism of setting loading as in ``wsgi.py`` is used in domain
specific ``manage.py``.

Domain-independent commands like ``collectstatic`` can be executed by the
main ``manage.py`` file in the repository root.
