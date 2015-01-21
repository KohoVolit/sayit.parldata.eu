------------
Installation
------------

#. Install elasticsearch_:

    .. _elasticsearch: http://elasticsearch.org

    .. code-block:: console
        $ cd /tmp
        $ wget -qO - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -
        $ sudo echo 'deb http://packages.elasticsearch.org/elasticsearch/1.4/debian stable main' | sudo tee /etc/apt/sources.list.d/elasticsearch.list
        $ sudo apt-get update
        $ sudo apt-get install elasticsearch

    Set its automatic start on system bootup:

    .. code-block:: console
        $ sudo update-rc.d elasticsearch defaults 95 10

    and restart system.

#. Install PostgreSQL_:

    .. _PostgreSQL: http://www.postgresql.org/

    .. code-block:: console
        $ sudo apt-get install postgresql postgresql-server-dev-9.3

#. Install packages needed for thumbnails to work correctly (needed by
Pillow used by Django easy_thumbnail application):

    .. code-block:: console
        $ sudo apt-get install libtiff4-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev python-tk

#. Install sayit.parldata.eu repository into a virtual environment:

    .. code-block:: console
        $ virtualenv /home/projects/.virtualenvs/sayit --no-site-packages
        $ source /home/projects/.virtualenvs/sayit/bin/activate
        $ sudo git clone https://github.com/mysociety/sayit_parldata_eu.git sayit
        $ cd /home/projects/sayit
        $ sudo pip install -r requirements.txt
        $ sudo pip install -e .[develop]
        $ sudo pip install python-dateutil lxml
        $ ./manage.py collectstatic --noinput
        $ deactivate

    Create a PostgreSQL user (with a real password instead of the example
one):

    .. code-block:: console
        $ sudo -u postgres psql
        postgres=# CREATE USER sayit WITH password 'sayit';

    Create a file with private settings and adjust its content:

    .. code-block:: console
        $ cp conf/private-example.yml conf/private.yml

#. Set-up Apache configuration:

    .. code-block:: console
        $ sudo mkdir /var/www/sayit.parldata.eu
        $ sudo chown :www-data /var/www/sayit.parldata.eu
        $ sudo chmod g+w /var/www/sayit.parldata.eu
        $ cp /home/projects/sayit/sayit.parldata.eu-example.conf /etc/apache2/sites-available/sayit.parldata.eu.conf
        $ sudo mkdir /var/log/apache2/sayit.parldata.eu
        $ sudo a2ensite sayit.parldata.eu
        $ sudo service apache2 reload

And finally, `add your parliaments`_.

.. _`add your parliaments`: README.rst#adding-of-a-new-parliament
