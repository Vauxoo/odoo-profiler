# -*- coding: utf-8 -*-

import base64
import logging
import os
import pstats
from contextlib import contextmanager
from datetime import datetime
from cProfile import Profile
from cStringIO import StringIO

from openerp import api, exceptions, fields, models, sql_db, tools

DATETIME_FORMAT_FILE = "%Y%m%d_%H%M%S"
CPROFILE_EMPTY_CHARS = b"{0"
PGOPTIONS = (
    '-c client_min_messages=notice -c log_min_messages=warning '
    '-c log_min_error_statement=error '
    '-c log_min_duration_statement=0 -c log_connections=on '
    '-c log_disconnections=on -c log_duration=off '
    '-c log_error_verbosity=verbose -c log_lock_waits=on '
    '-c log_statement=none -c log_temp_files=0 '
)
PGOPTIONS_PREDEFINED = os.environ.get('PGOPTIONS') and True or False
DFTL_LOG_PATH = os.environ.get('PG_LOG_PATH', 'postgresql.log')


_logger = logging.getLogger(__name__)


class ProfilerProfile(models.Model):
    _name = 'profiler.profile'

    name = fields.Char()
    enable_python = fields.Boolean(default=True,
                                   states={'enabled': [('readonly', True)]})
    enable_postgresql = fields.Boolean(
        default=False,
        states={'enabled': [('readonly', True)]},
        help="It requires postgresql server logs seudo-enabled")
    use_index = fields.Boolean(
        default=False,
        help="Index human-readable cProfile attachment."
        "\nWarning: Uses more resources.")
    date_started = fields.Char(readonly=True)
    date_finished = fields.Char(readonly=True)
    state = fields.Selection([
        ('enabled', 'Enabled'),
        ('disabled', 'Disabled'),
    ], default='disabled', readonly=True)
    description = fields.Text(readonly=True)

    @api.onchange('enable_postgresql')
    def onchange_enable_postgresql(self):
        if not self.enable_postgresql:
            return
        self.description = (
            "You need seudo-enable logs from your "
            "postgresql-server configuration file.\n"
            "Common paths:\n\t-/etc/postgresql/VERSION/main/postgresql.conf\n"
            "or your can looking for the service using: "
            "'ps aux | grep postgres'\n\n"
        )
        self.description += """Adds the following parameters:
# Pre-enable logs
logging_collector=on
log_destination='stderr'
log_directory='pg_log'
log_filename='postgresql.log'
log_rotation_age=0
log_checkpoints=on
log_hostname=on
log_line_prefix='%t [%p]: [%l-1] db=%d,user=%u '

Requires restart postgresql server service.

NOTE: This module will enable the following parameter from the client:
    It's not needed added them to configuration file.
# Enable logs
client_min_messages=notice
log_min_messages=warning
log_min_error_statement=error
log_min_duration_statement=0
log_connections=on
log_disconnections=on
log_duration=off
log_error_verbosity=verbose
log_lock_waits=on
log_statement=none
log_temp_files=0
"""

    # TODO: Schedule a profiling in the future for a range of dates
    # TODO: One profile by each profiler.profile record
    profile = Profile()
    # TODO: multi-profiles
    enabled = False

    @api.model
    def now_utc(self):
        self.env.cr.execute("SELECT to_char(now(), 'YYYY-MM-DD HH24:MI:SS')")
        now = self.env.cr.fetchall()[0][0]
        # now = fields.Datetime.to_string(
        #     fields.Datetime.context_timestamp(self, datetime.now()))
        return now

    @api.multi
    def enable(self):
        self.ensure_one()
        if tools.config.get('workers'):
            raise exceptions.UserError(
                "Start the odoo server using the parameter '--workers=0'")
        _logger.info("Enabling profiler")
        self.write(dict(
            date_started=self.now_utc(),
            state='enabled'
        ))
        ProfilerProfile.enabled = self.enable_python
        self._reset_postgresql()

    @api.multi
    def _reset_postgresql(self):
        if PGOPTIONS_PREDEFINED or not self.enable_postgresql:
            _logger.info("Using PGOPTIONS predefined.")
            return
        pg_options = PGOPTIONS if self.state == 'enabled' else None
        os.environ['PGOPTIONS'] = PGOPTIONS
        self._reset_connection()

    def _reset_connection(self):
        """This method cleans (rollback) all current transactions over actual
        cursor in order to avoid errors with waiting transactions.
            - request.cr.rollback()
        Also connections on current database's only are closed by the next
        statement
            - dsn = odoo.sql_db.connection_info_for(request.cr.dbname)
            - odoo.sql_db._Pool.close_all(dsn[1])
        Otherwise next error will be trigger
        'InterfaceError: connection already closed'
        Finally new cursor is assigned to the request object, this cursor will
        take the os.environ setted. In this case the os.environ is setted with
        all 'PGOPTIONS' required to log all sql transactions in postgres.log
        file.
        If this method is called one more time, it will create a new cursor and
        take the os.environ again, this is usefully if we want to reset
        'PGOPTIONS'
        """
        cr = self.env.cr
        dbname = cr.dbname
        cr.commit()
        dsn = sql_db.connection_info_for(dbname)
        sql_db._Pool.close_all(dsn[1])
        db = sql_db.db_connect(dbname)
        self.env.cr = db.cursor()

    def get_stats_string(self, cprofile_path):
        pstats_stream = StringIO()
        pstats_obj = pstats.Stats(cprofile_path, stream=pstats_stream)
        pstats_obj.sort_stats('cumulative')
        pstats_obj.print_stats()
        pstats_stream.seek(0)
        stats_string = pstats_stream.read()
        pstats_stream = None
        return stats_string

    @api.multi
    def dump_postgresql_logs(self, indexed=None):
        self.ensure_one()
        # TODO: Run pgbadger command if It's running postgresql locally
        started = fields.Datetime.from_string(
            self.date_started).strftime(DATETIME_FORMAT_FILE)
        finished = fields.Datetime.from_string(
            self.date_finished).strftime(DATETIME_FORMAT_FILE)

        fname = "postgresql_log_pgbadger_%d_%s_to_%s" % (
            self.id, started, finished
        )
        pgbadger_bin = "pgbadger"
        pgbadger_cmd = [
            pgbadger_bin, '-f', 'stderr', '-T', fname,
            '-o', fname + '.html', '-d', self.env.cr.dbname,
            '-b', self.date_started,
            '-e', self.date_finished, '--sample', '4',
            '--quiet', DFTL_LOG_PATH]
        pgbadger_cmd_s = pgbadger_bin + ' ' + ' '.join([
            param if param.startswith('-') else '"%s"' % param
            for param in pgbadger_cmd[1:]])
        self.description = (
        "Locate postgresql.log from your postgresql-server.\n"
        "\nDefault paths:\n\t "
        "- /var/lib/postgresql/VERSION/main/pg_log/postgresql.log\n\t"
        "- /var/log/pg_log/postgresql.log\n\t"
        "\nInstall 'apt-get install pgbadger'"
        "\nRun the following command:\n%s") % pgbadger_cmd_s

    @api.model
    def dump_stats(self, started, finished, indexed=None):
        attachment = None
        with tools.osutil.tempdir() as dump_dir:
            started = fields.Datetime.from_string(
                started).strftime(DATETIME_FORMAT_FILE)
            finished = fields.Datetime.from_string(
                finished).strftime(DATETIME_FORMAT_FILE)
            cprofile_fname = 'stats_%d_%s_to_%s.cprofile' % (
                self.id, started, finished)
            cprofile_path = os.path.join(dump_dir, cprofile_fname)
            _logger.info("Dumping cProfile '%s'", cprofile_path)
            ProfilerProfile.profile.dump_stats(cprofile_path)
            with open(cprofile_path, "rb") as f_cprofile:
                datas = f_cprofile.read()
            if datas and datas != CPROFILE_EMPTY_CHARS:
                attachment = self.env['ir.attachment'].create({
                    'name': cprofile_fname,
                    'res_id': self.id,
                    'res_model': self._name,
                    'datas': base64.encodestring(datas),
                    'datas_fname': cprofile_fname,
                    'description': 'cProfile dump stats',
                })
                try:
                    if indexed:
                        attachment.index_content = (
                            self.get_stats_string(cprofile_path))
                except:
                    # Fancy feature but not stop process if fails
                    pass
                self.dump_postgresql_logs()
                _logger.info("cProfile stats stored.")
            else:
                _logger.info("cProfile stats empty.")
        return attachment

    @api.multi
    def clear(self, reset_date=True):
        self.ensure_one()
        _logger.info("Clear profiler")
        if reset_date:
            self.date_started = self.now_utc()
        ProfilerProfile.profile.clear()

    @api.multi
    def disable(self):
        self.ensure_one()
        _logger.info("Disabling profiler")
        self.state = 'disabled'
        self.date_finished = self.now_utc()
        self.dump_stats(self.date_started, self.date_finished, self.use_index)
        self.clear(reset_date=False)
        ProfilerProfile.enabled = False
        self._reset_postgresql()

    @staticmethod
    @contextmanager
    def profiling():
        """Thread local profile management, according to the shared "enabled"
        """
        if ProfilerProfile.enabled:
            _logger.debug("Catching profiling")
            ProfilerProfile.profile.enable()
        try:
            yield
        finally:
            if ProfilerProfile.enabled:
                ProfilerProfile.profile.disable()

    @api.multi
    def action_view_attachment(self):
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', self._name), ('res_id', '=', self.id)])
        action = self.env.ref("base.action_attachment").read()[0]
        action['domain'] = [('id', 'in', attachments.ids)]
        return action
