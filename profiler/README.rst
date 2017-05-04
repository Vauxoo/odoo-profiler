.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============
Odoo Profiler
=============

This module is an integration of cprofile for Odoo.
Check the Profiler menu in admin menu

Configuration
=============
By default profiler module adds two system parameters
    - exclude_fnames > '/.repo_requirements,~/odoo-8.0,/usr/,>'
    - exclude_query > 'ir_translation'.

These parameters can be configurated in order to exclude some outputs from
profiling stats or pgbadger output.

Credits
=======

Contributors
------------

* Moisés López <moylop260@vauxoo.com>
* Hugo Adan <hugo@vauxoo.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
