# -*- coding: utf-8 -*-

import base64
import logging
import os
import pstats
from contextlib import contextmanager
from cProfile import Profile
from cStringIO import StringIO

from psycopg2 import OperationalError, ProgrammingError

from openerp import api, exceptions, fields, models, sql_db, tools

DATETIME_FORMAT_FILE = "%Y%m%d_%H%M%S"
CPROFILE_EMPTY_CHARS = b"{0"
PGOPTIONS = {
    'log_min_duration_statement': '0',
    'client_min_messages': 'notice',
    'log_min_messages': 'warning',
    'log_min_error_statement': 'error',
    'log_duration': 'off',
    'log_error_verbosity': 'verbose',
    'log_lock_waits': 'on',
    'log_statement': 'none',
    'log_temp_files': '0',
}
PGOPTIONS_ENV = ' '.join(["-c %s=%s" % (param, value)
                          for param, value in PGOPTIONS.items()])
DFTL_LOG_PATH = os.environ.get('PG_LOG_PATH', 'postgresql.log')


_logger = logging.getLogger(__name__)


class ProfilerProfile(models.Model):
    # TODO: Add constraint to avoid 2 or more enabled profiles
    _name = 'profiler.profile'

    name = fields.Char()
    enable_python = fields.Boolean(default=True)
    enable_postgresql = fields.Boolean(
        default=False,
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
    ], default='disabled', readonly=True, required=True)
    description = fields.Text(readonly=True)
    attachment_count = fields.Integer(compute="_compute_attachment_count")

    @api.multi
    def _compute_attachment_count(self):
        for record in self:
            self.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name), ('res_id', '=', record.id)])

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
log_connections=on
log_disconnections=on

Reload configuration using the following query:
 - select pg_reload_conf()
Or restart the postgresql server service.

FYI This module will enable the following parameter from the client
    It's not needed added them to configuration file if database user is superuser
     or use PGOPTIONS environment variable in the terminal that you start
     your odoo server.
    If you don't add these parameters or PGOPTIONS this module will try do it.
# Enable logs from postgresql.conf
log_min_duration_statement=0
client_min_messages=notice
log_min_messages=warning
log_min_error_statement=error
log_duration=off
log_error_verbosity=verbose
log_lock_waits=on
log_statement=none
log_temp_files=0

#  Or enable logs from PGOPTIONS environment variable before to start odoo server
export PGOPTIONS="-c log_min_duration_statement=0 -c client_min_messages=notice -c log_min_messages=warning -c log_min_error_statement=error -c log_connections=on -c log_disconnections=on -c log_duration=off -c log_error_verbosity=verbose -c log_lock_waits=on -c log_statement=none -c log_temp_files=0"
~/odoo_path/odoo-bin ...
"""

    profile = Profile()
    enabled = None
    pglogs_enabled = None

    # True to activate it False to inactivate None to do nothing
    activate_deactivate_pglogs = None

    # Params dict with values before to change it.
    psql_params_original = {}

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
        if not self.enable_postgresql:
            return
        if ProfilerProfile.pglogs_enabled:
            _logger.info("Using postgresql.conf or PGOPTIONS predefined.")
            return
        os.environ['PGOPTIONS'] = (
            PGOPTIONS_ENV if self.state == 'enabled' else '')
        self._reset_connection(self.state == 'enabled')

    def _reset_connection(self, enable):
        for connection in sql_db._Pool._connections:
            with connection[0].cursor() as pool_cr:
                params = (PGOPTIONS if enable
                          else ProfilerProfile.psql_params_original)
                for param, value in params.items():
                    try:
                        pool_cr.execute('SET %s TO %s' % (param, value))
                    except (OperationalError, ProgrammingError) as oe:
                        pool_cr.connection.rollback()
                        raise exceptions.UserError(
                                "It's not possible change parameter.\n%s\n"
                                "Please, disable postgresql or re-enable it "
                                "in order to read the instructions" % str(oe))
            ProfilerProfile.activate_deactivate_pglogs = enable

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

    @api.model
    def set_pgoptions_enabled(self):
        """Verify if postgresql has configured the parameters for logging"""
        ProfilerProfile.pglogs_enabled = True
        pgoptions_enabled = bool(os.environ.get('PGOPTIONS'))
        _logger.info('Logging enabled from environment '
                     'variable PGOPTIONS? %s', pgoptions_enabled)
        if pgoptions_enabled:
            return
        pgparams_required = {
            'log_min_duration_statement': '0',
        }
        for param, value in pgparams_required.items():
            self.env.cr.execute("SHOW %s" % param)
            db_value = self.env.cr.fetchone()[0].lower()
            if value.lower() != db_value:
                ProfilerProfile.pglogs_enabled = False
                break
        ProfilerProfile.psql_params_original = self.get_psql_params(
            self.env.cr, PGOPTIONS.keys())
        _logger.info('Logging enabled from postgresql.conf? %s',
                     ProfilerProfile.pglogs_enabled)

    @staticmethod
    def get_psql_params(cr, params):
        result = {}
        for param in set(params):
            cr.execute('SHOW %s' % param)
            result.update(cr.dictfetchone())
        return result

    @api.model
    def _setup_complete(self):
        self.set_pgoptions_enabled()
        return super(ProfilerProfile, self)._setup_complete()
