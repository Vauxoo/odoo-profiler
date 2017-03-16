cProfile integration for OpenERP
================================

The module ``profiler`` provides a very basic integration of
the standard ``cProfile`` into OpenERP/Odoo.

Basic usage
-----------

After installation, a player is add on the header bar, with
four items:

|player|

* Start profiling |start_profiling|
* Stop profiling |stop_profiling|
* Download stats: download stats file |dump_stats|
* Clear stats |clear_stats|

Advantages
----------

Executing Python code under the profiler is not really hard, but this
module allows to do it in OpenERP context such that:

* no direct modification of main server Python code or addons is needed
  (although it could be pretty simple depending on the need)
* subtleties about threads are taken care of. In particular, the
  accumulation of stats over several requests is correct.
* Quick access UI to avoid statistics pollution
* Use the standard cProfile format, see Python documentation and performance
  wiki page for exploitation tips. Also do not miss `RunSnakeRun 
  <http://www.vrplumber.com/programming/runsnakerun/>`_ GUI tool to help you to
  interpret it easly.

Caveats
-------

* enabling the profile in one database actually does it for the whole
  instance
* multiprocessing (``--workers``) is *not* taken into account
* currently developped and tested with OpenERP 10.0 only
* no special care for uninstallion : currently a restart is needed to
  finish uninstalling.
* requests not going through web controllers are currently not taken
  into account
  
Requirements
------------

* Install `pgbadger <http://dalibo.github.io/pgbadger/>`_ binary package.
* Install `pstats_print2list <https://pypi.python.org/pypi/pstats_print2list>`_ python package.
* Enable postgresql logs from postgresql's configuration file (Default location for Linux Debian is `/etc/postgresql/*/main/postgresql.conf`)
 - Add the following lines at final (A postgresql restart is required `/etc/init.d/postgresql restart`)

.. code-block:: text

 logging_collector=on
 log_destination='stderr'
 log_directory='pg_log'
 log_filename='postgresql.log'
 log_rotation_age=0
 log_checkpoints=on
 log_hostname=on
 log_line_prefix='%t [%p]: [%l-1] db=%d,user=%u '


Credit
------

Remotely inspired from ZopeProfiler, although there is no online
visualisation and there may never be one.

This is a fork from https://bitbucket.org/anybox/odoo_profiler now maintained by Vauxoo.

.. |player| image:: https://bytebucket.org/anybox/odoo_profiler/raw/default/doc/static/player.png
    :alt: Player to manage profiler
.. |start_profiling| image:: https://bytebucket.org/anybox/odoo_profiler/raw/default/doc/static/start_profiling.png
    :alt: Start profiling
    :height: 35px
.. |stop_profiling| image:: https://bytebucket.org/anybox/odoo_profiler/raw/default/doc/static/stop_profiling.png
    :alt: Stop profiling
    :height: 35px
.. |dump_stats| image:: https://bytebucket.org/anybox/odoo_profiler/raw/default/doc/static/dump_stats.png
    :alt: Download cprofile stats file
    :height: 35px
.. |clear_stats| image:: https://bytebucket.org/anybox/odoo_profiler/raw/default/doc/static/clear_stats.png
    :alt: Clear and remove stats file
    :height: 35px
