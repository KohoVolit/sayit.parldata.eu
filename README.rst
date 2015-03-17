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

The WSGI application extracts the parliament from *WSGIProcessGroup*
directive in the subdomain's virtual host section of the Apache
configuration file and it imports parliament-specific settings. Thus
WSGI processes for all subdomains share the same Django project where
they add their specific settings on initialization.

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

#.  Copy one of the files in ``/subdomains`` directory and adjust its
    content for the new parliament.

#.  Create database tables:

    .. code-block:: console

        $ source /home/projects/.virtualenvs/sayit/bin/activate
        (sayit)$ ./manage.py syncdb --settings subdomains.<your-parliament>
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

#.  Based on the ElasticSearch indexing settings for the new parliament
    you may need to add some files for a new language to ElasticSearch
    config path (usually ``/etc/elasticsearch`` or
    ``/usr/share/elasticsearch/config``) and restart it. Those files for
    some languages are in ``/conf/elasticsearch`` subdirectory in the
    repo.

    Some useful resources on configuring languages in Elasticsearch:
    * `Snowball Token Filter`_
    * `LemmaGen Analysis for ElasticSearch`_
    * `Elasticsearch: Vyhledáváme hezky česky (a taky slovensky)`_
    * `Morfologik (Polish) Analysis for ElasticSearch`_
    * `stop-words lists for many languages`_

    .. _`Snowball Token Filter`: http://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-snowball-tokenfilter.html
    .. _`LemmaGen Analysis for ElasticSearch`: https://github.com/vhyza/elasticsearch-analysis-lemmagen
    .. _`Elasticsearch: Vyhledáváme hezky česky (a taky slovensky)`: http://www.zdrojak.cz/clanky/elasticsearch-vyhledavame-hezky-cesky-ii-a-taky-slovensky/
    .. _`Morfologik (Polish) Analysis for ElasticSearch`: https://github.com/monterail/elasticsearch-analysis-morfologik
    .. _`stop-words lists for many languages`: https://code.google.com/p/stop-words/source/browse/trunk/stop-words/stop-words-collection-2014.02.24/stop-words


Importing of data
=================

Data are imported from ``api.parldata.eu`` via commandline script
``manage.py`` using the command ``load_parldata`` and the subdomain
specified in ``--settings`` option. Running the command without
specifying a subdomain imports data for all subdomains. The script must
be executed in virtual environment of the installation and as the user
running the webserver (because of Caching_).

Quality of debates data at ``api.parldata.eu`` for all parliaments may
be checked before initial import by a simple script
``check_debates_data.py`` at ``sayit_parldata_eu/importers``
subdirectory.


Example
-------

To initially import data for Slovak parliament subdomain:

.. code-block:: console

    $ source /home/projects/.virtualenvs/sayit/bin/activate
    (sayit)$ sudo -u www-data /home/projects/sayit/manage.py load_parldata --settings subdomains.sk_nrsr --initial

To load new data since the last import for all subdomains:

.. code-block:: console

    (sayit)$ sudo -u www-data /home/projects/sayit/manage.py load_parldata

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
``manage.py collectstatic`` and ``manage.py refresh_cache`` after any
CSS modification.

.. _`SayIt uses`: http://mysociety.github.io/sayit/develop/


Settings loading
----------------

All instances corresponding to the subdomains share the same codebase and
the same Django project. Each subdomain has its own ``VirtualHost`` block
in Apache config file and its own settings in the ``subdomains``
directory. The settings for a particular subdomain are loaded as follows:

The WSGI application extracts the parliament from *WSGIProcessGroup*
directive that is unique in each ``VirtualHost`` block and it imports
settings for that parliament from ``subdomains/<parliament>.py``. There
are some parliament-specific settings and then the main file with common
settings is imported in a way that passes the specific ones. The common
settings file loads private settings from ``conf/private.yml`` file that
is not present in the repository.

The same settings loading is used in ``manage.py``, only the module with
parliament-specific settings is provided by ``--settings`` directive.

For domain-independent ``manage.py`` commands like ``collectstatic`` the
``--settings`` directive is not needed.


Caching
-------

Rendering of templates for long debates (hundreds of speeches) may take
a long time. Because of that, caching is need.

Server-side caching on the filesystem is used for all section views and
the speakers list. Pages are rendered into cache in advance by the
import script for all imported or updated sections. Hence a user never
waits for a template to render, the page is always served from cache.

The cache must be manually refreshed after any modification of
application code that affects output of views or after any changes in
CSS. Refresh the cache for all subdomains by Django command:

.. code-block:: console

    (sayit)$ sudo -u www-data /home/projects/sayit/manage.py refresh_cache

Django's FileBasedCache creates files accessible only by the user who
created them. Because the cache is written by the import script and read
by the webserver, both have to run as the same user. Therefore the
import script and cache refreshment command must be executed as the
webserver user, eg. *www-data*.
