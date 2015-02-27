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
implement it differently.

A separate WSGI application runs for each parliament initialized with
parliament-specific settings. All WSGI applications share the same
codebase and the same Django project with common settings.

The following steps are needed to add a new parliament:

#.  Create a new database ``sayit_<country_code>_<parliament_code>``
    with collation settings corresponding to primary language of the
    parliament. Example:

    .. code-block:: SQL

        CREATE DATABASE sayit_sk_nrsr WITH LC_CTYPE 'sk_SK.UTF-8' LC_COLLATE 'sk_SK.UTF-8' TEMPLATE template0 OWNER sayit;

    When the required locale is missing in your system, create it first
    and restart database server:

    .. code-block:: console

        $ sudo locale-gen xx_YY.UTF-8
        $ sudo service postgresql restart

#.  Copy one of the subdirectories in ``/subdomains`` directory under a
    new name <country_code>_<parliament_code> and adjust content of the
    ``settings.py`` file within.

#.  Create database tables:

    .. code-block:: console

        $ source /home/projects/.virtualenvs/sayit/bin/activate
        (sayit)$ subdomains/sk_nrsr/manage.py syncdb
        (sayit)$ deactivate

#.  Connect to the new database and create additional indexes to speed-up
    regular data imports:

    .. code-block:: SQL

        CREATE INDEX speeches_section_source_url on speeches_section(source_url);
        CREATE INDEX speeches_speech_source_url on speeches_speech(source_url);

#.  Modify ``/etc/apache2/sites-available/sayit.parldata.eu.conf``, copy
    one of the ``VirtualHost`` blocks and edit the copy to correspond
    with the new parliament. Then

    .. code-block:: console

        $ sudo service apache2 reload

#.  Create a new Google Analytics property within the existing GA account
    and set the two-digit code of the property in the ``settings.py``
    file above.


Importing of data
=================

Data are imported from ``api.parldata.eu`` via commandline script
``manage.py`` of the particular subdomain and using the command
``load_parldata``. The script must be executed in virtual environment
of the installation and as the user running the webserver (because of
Caching_).

Quality of debates data at ``api.parldata.eu`` for all parliaments may
be checked before initial import by a simple script
``check_debates_data.py`` at ``sayit_parldata_eu/importers``
subdirectory.


Example
-------

To initially import data for Slovak parliament subdomain:

.. code-block:: console

    $ source /home/projects/.virtualenvs/sayit/bin/activate
    (sayit)$ sudo -u www-data /home/projects/sayit/subdomains/sk_nrsr/manage.py load_parldata --initial

To load new data since the last import:

.. code-block:: console

    (sayit)$ sudo -u www-data /home/projects/sayit/subdomains/sk_nrsr/manage.py load_parldata

Schedule the incremental update to be executed by Cron if regular
updates are needed.


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
WSGI application file ``subdomains/<parliament>/wsgi.py`` which loads
settings file from the same directory. The settings file imports common
settings from ``sayit_parldata_eu/settings/base.py`` and overrides the
parliament-specific ones. The common settings file loads private settings
from ``conf/private.yml`` file that is not present in the repository.

The same mechanism of settings loading as in ``wsgi.py`` is used in
domain specific ``manage.py``.

Domain-independent commands like ``collectstatic`` can be executed by the
main ``manage.py`` file in the repository root.


Caching
-------

Rendering of templates for long debates may take a long time. It takes
10-20s for sittings with hundreds of speeches. Because of that, caching
is need.

Server-side caching on the filesystem is used for all section views and
the speakers list. Pages are rendered into cache in advance by the
import script for all imported or updated sections. Hence a user never
waits for a template to render, the page is always served from cache.

Django's FileBasedCache creates files accessible only by the user who
created them. Because the cache is written by the import script and read
by the webserver, both have to run as the same user. Therefore the
import script must be executed as the webserver user, eg. *www-data*.
