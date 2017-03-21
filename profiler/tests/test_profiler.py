# coding: utf-8
# License AGPL-3 or later (http://www.gnu.org/licenses/lgpl).
# Copyright 2014 Anybox <http://anybox.fr>
# Copyright 2016 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>

import openerp.tests


@openerp.tests.common.at_install(False)
@openerp.tests.common.post_install(True)
class TestUi(openerp.tests.HttpCase):
    def test_01_admin_profiler_tour(self):
        self.phantom_js(
            "/",
            "odoo.__DEBUG__.services['web.Tour'].run('profile')",
            "odoo.__DEBUG__.services['web.Tour'].tours.profile",
            login="admin")
