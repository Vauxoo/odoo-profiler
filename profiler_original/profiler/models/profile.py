# coding: utf-8
# License AGPL-3 or later (http://www.gnu.org/licenses/lgpl).
# Copyright 2014 Anybox <http://anybox.fr>
# Copyright 2016 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>

from openerp import fields, models


class ProfilerProfile(models.Model):
    _name = 'profiler.profile'

    enable_postgresql = fields.Boolean()
    enable_python = fields.Boolean()
    date_started = fields.Char(readonly=True)
    date_finished = fields.Char(readonly=True)

    def enable(self):
        self.write(dict(
            date_started=fields.Datetime.now
        ))

    def disable(self):
        self.write(dict(
            date_finished=fields.Datetime.now
        ))
