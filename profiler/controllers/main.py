# coding: utf-8
# License AGPL-3 or later (http://www.gnu.org/licenses/lgpl).
# Copyright 2014 Anybox <http://anybox.fr>
# Copyright 2016 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
import errno
import logging
import os
import shutil
import tempfile
import sys

from datetime import datetime
from cStringIO import StringIO
from pstats_print2list import get_pstats_print2list, print_pstats_list

from odoo.tools.misc import find_in_path
from odoo import http, tools
from odoo.http import request, content_disposition

from odoo.addons.profiler.hooks import CoreProfile as core

_logger = logging.getLogger(__name__)
DFTL_LOG_PATH = '/var/lib/postgresql/9.5/main/pg_log/postgresql.log'
# PGOPTIONS = (' -c client_min_messages=notice -c log_min_messages=warning '
#              '-c log_min_error_statement=error '
#              '-c log_min_duration_statement=0 -c log_connections=on '
#              '-c log_disconnections=on -c log_duration=off '
#              '-c log_error_verbosity=verbose -c log_lock_waits=on '
#              '-c log_statement=none -c log_temp_files=0')

PG_OPTIONS = {
    # Index 0 is custom value Index 1 original value
    'SHOW client_min_messages': ["SET client_min_messages='notice'",
                                 "SET client_min_messages='notice'"],
    'SHOW log_min_messages': ["SET log_min_messages='warning'",
                              "SET log_min_messages='warning'"],
    'SHOW log_min_error_statement': ["SET log_min_error_statement='error'",
                                     "SET log_min_error_statement='error'"],
    'SHOW log_min_duration_statement': ["SET log_min_duration_statement=0",
                                        "SET log_min_duration_statement=-1"],
    # *** OperationalError: parameter "log_connections|log_disconnections"
    # cannot be set after connection start
    # 'SHOW log_connections': ["SET log_connections=true",
    #                          "SET log_connections=false"],
    # 'SHOW log_disconnections': ["SET log_disconnections=true",
    #                             "SET log_disconnections=false"],
    'SHOW log_duration': ["SET log_duration=false",
                          "SET log_duration=false"],
    'SHOW log_error_verbosity': ["SET log_error_verbosity='verbose'",
                                 "SET log_error_verbosity='default'"],
    'SHOW log_lock_waits': ["SET log_lock_waits=true",
                            "SET log_lock_waits=false"],
    'SHOW log_statement': ["SET log_statement=none",
                           "SET log_statement=none"],
    'SHOW log_temp_files': ["SET log_temp_files=0",
                            "SET log_temp_files=-1"]}


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout


class ProfilerController(http.Controller):

    _cp_path = '/web/profiler'

    player_state = 'profiler_player_clear'
    begin_date = ''
    end_date = ''
    """Indicate the state(css class) of the player:

    * profiler_player_clear
    * profiler_player_enabled
    * profiler_player_disabled
    """

    @http.route(['/web/profiler/enable'], type='json', auth="user")
    def enable(self):
        _logger.info("Enabling")
        core.enabled = True
        ProfilerController.begin_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")
        ProfilerController.player_state = 'profiler_player_enabled'
        # os.environ.setdefault('PGOPTIONS', PGOPTIONS)
        self.pg_enable()

    @http.route(['/web/profiler/disable'], type='json', auth="user")
    def disable(self, **post):
        _logger.info("Disabling")
        core.enabled = False
        ProfilerController.end_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")
        ProfilerController.player_state = 'profiler_player_disabled'
        # if os.environ.get('PGOPTIONS', False):
        #     del os.environ['PGOPTIONS']
        self.pg_disable()

    @http.route(['/web/profiler/clear'], type='json', auth="user")
    # @http.jsonrequest
    def clear(self, **post):
        core.profile.clear()
        _logger.info("Cleared stats")
        ProfilerController.player_state = 'profiler_player_clear'
        ProfilerController.end_date = ''
        ProfilerController.begin_date = ''

    # @http.httprequest
    @http.route(['/web/profiler/dump'], type='http', auth="user")
    def dump(self, token, **post):
        """Provide the stats as a file download.

        Uses a temporary file, because apparently there's no API to
        dump stats in a stream directly.
        """
        exclude_fname = self.get_exclude_fname()
        with tools.osutil.tempdir() as dump_dir:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = 'openerp_%s' % ts
            stats_path = os.path.join(dump_dir, '%s.stats' % filename)
            core.profile.dump_stats(stats_path)
            _logger.info("Pstats Command:")
            params = {'fnames': stats_path, 'sort': 'cumulative', 'limit': 45,
                      'exclude_fnames': exclude_fname}
            _logger.info(
                "fnames=%(fnames)s, sort=%(sort)s,"
                " limit=%(limit)s, exclude_fnames=%(exclude_fnames)s", params)
            pstats_list = get_pstats_print2list(**params)
            with Capturing() as output:
                print_pstats_list(pstats_list)
            result_path = os.path.join(dump_dir, '%s.txt' % filename)
            with open(result_path, "a") as res_file:
                for line in output:
                    res_file.write('%s\n' % line)
            # PG_BADGER
            self.dump_pgbadger(dump_dir, 'pgbadger_output.txt')
            t_zip = tempfile.TemporaryFile()
            tools.osutil.zip_dir(dump_dir, t_zip, include_dir=False)
            t_zip.seek(0)
            headers = [
                ('Content-Type', 'application/octet-stream; charset=binary'),
                ('Content-Disposition', content_disposition(
                    '%s.zip' % filename))]
            _logger.info('Download Profiler zip: %s', t_zip.name)
            return request.make_response(
                t_zip, headers=headers, cookies={'fileToken': token})

    @http.route(['/web/profiler/initial_state'], type='json', auth="user")
    def initial_state(self, **post):
        user = request.env['res.users'].browse(request.uid)
        return {
            'has_player_group': user.has_group(
                'profiler.group_profiler_player'),
            'player_state': ProfilerController.player_state,
        }

    def dump_pgbadger(self, dir_dump, output):
        pgbadger = find_in_path("pgbadger")
        if not pgbadger:
            _logger.error("Pgbadger not found")
            return
        filename = os.path.join(dir_dump, output)
        logfilename = os.path.join(dir_dump, 'postgresql.log')
        log_path = os.environ.get('PG_LOG_PATH', DFTL_LOG_PATH)
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:
                # error is different than File exists
                if exc.errno != errno.EEXIST:
                    _logger.error("File can be created")
                    return
        shutil.copyfile(log_path, logfilename)
        _logger.info("Generating PG Badger report.")
        exclude_query = self.get_exclude_query()
        command = [
            pgbadger, '-f', 'stderr', '-T', 'Odoo-Profiler',
            '-o', '-', '-b', ProfilerController.begin_date,
            '-e', ProfilerController.end_date, '--sample', '2',
            '--disable-type', '--disable-error', '--disable-hourly',
            '--disable-session', '--disable-connection',
            '--disable-temporary', '--quiet']
        command.extend(exclude_query)
        command.append(log_path)

        _logger.info("Pgbadger Command:")
        _logger.info(command)
        # my_env = os.environ.copy()
        # result = _exec_pipe(command[0], command[1:], my_env)
        # result = tools.exec_command_pipe(command[0], command[1:],
        #                                  my_env)
        result = tools.exec_command_pipe(*command)
        with open(filename, 'w') as fw:
            fw.write(result[1].read())
        _logger.info("Done")

    def get_exclude_fname(self):
        efnameid = request.env.ref(
            'profiler.default_exclude_fnames_pstas', raise_if_not_found=False)
        if not efnameid:
            return []
        return [os.path.expanduser(path)
                for path in efnameid and efnameid.value.strip(',').split(',')
                if path]

    def get_exclude_query(self):
        """Example '^(COPY|COMMIT)'
        """
        equeryid = request.env.ref(
            'profiler.default_exclude_query_pgbadger',
            raise_if_not_found=False)
        if not equeryid:
            return []
        exclude_queries = []
        for path in equeryid and equeryid.value.strip(',').split(','):
            exclude_queries.extend(
                ['--exclude-query', '"^(%s)" ' % path.encode('UTF-8')])
        return exclude_queries

    def pg_enable(self):
        for option in PG_OPTIONS:
            request.cr.execute(PG_OPTIONS[option][0])

    def pg_disable(self):
        for option in PG_OPTIONS:
            request.cr.execute(PG_OPTIONS[option][1])
