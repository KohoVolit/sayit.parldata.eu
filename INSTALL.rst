------------
Installation
------------

#.  Install elasticsearch_:

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

    and restart system:

    .. code-block:: console

        $ sudo reboot

#.  Install PostgreSQL_:

    .. _PostgreSQL: http://www.postgresql.org/

    .. code-block:: console

        $ sudo apt-get install postgresql postgresql-server-dev-9.3

#.  Install packages needed for thumbnails to work correctly (needed by
    Pillow used by Django easy_thumbnail application):

    .. code-block:: console

        $ sudo apt-get install libtiff4-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev python-tk

#.  Install sayit.parldata.eu repository into a virtual environment:

    .. code-block:: console

        $ virtualenv /home/projects/.virtualenvs/sayit --no-site-packages
        $ source /home/projects/.virtualenvs/sayit/bin/activate
        (sayit)$ sudo git clone https://github.com/KohoVolit/sayit.parldata.eu.git sayit
        (sayit)$ cd /home/projects/sayit
        (sayit)$ sudo wget -P sayit_parldata_eu/importers https://raw.githubusercontent.com/KohoVolit/api.parldata.eu/master/client/vpapi.py
        (sayit)$ sudo wget -P sayit_parldata_eu/importers https://raw.githubusercontent.com/KohoVolit/api.parldata.eu/master/client/server_cert.pem
        (sayit)$ sudo pip install -r requirements.txt

    Create a PostgreSQL user (with a real password instead of the example
    one):

    .. code-block:: console

        (sayit)$ sudo -u postgres psql
        (sayit)postgres=# CREATE USER sayit WITH password 'sayit';

    Create a file with private settings and adjust its content:

    .. code-block:: console

        (sayit)$ cp conf/private-example.yml conf/private.yml

    Create directory for logs:

    .. code-block:: console

        $ sudo mkdir -m 775 /var/log/sayit
        $ sudo chown visegrad:www-data /var/log/sayit

    Collect static files of the project:

    .. code-block:: console

        (sayit)$ sudo mkdir -m 775 /var/www/sayit.parladata.eu
        (sayit)$ sudo chown visegrad:www-data /var/www/sayit.parldata.eu
        (sayit)$ ./manage.py collectstatic --noinput
        (sayit)$ deactivate

#.  Set-up Apache configuration:

    .. code-block:: console

        $ sudo cp /home/projects/sayit/conf/sayit.parldata.eu-example.conf /etc/apache2/sites-available/sayit.parldata.eu.conf
        $ sudo mkdir /var/log/apache2/sayit.parldata.eu
        $ sudo a2ensite sayit.parldata.eu
        $ sudo service apache2 reload

And finally, `add your parliaments`_.

.. _`add your parliaments`: README.rst#adding-of-a-new-parliament
