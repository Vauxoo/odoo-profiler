# coding: utf-8
import errno
import logging
import os
import subprocess
import shutil
import tempfile
import sys

from datetime import datetime
from cStringIO import StringIO
from pstats_print2list import get_pstats_print2list, print_pstats_list

from odoo.tools.misc import find_in_path
from odoo import http, tools
from odoo.http import request, content_disposition

from . import core

_logger = logging.getLogger(__name__)


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
    """Indicate the state(css class) of the player:

    * profiler_player_clear
    * profiler_player_enabled
    * profiler_player_disabled
    """

    @http.route(['/web/profiler/enable'], type='json', auth="user")
    def enable(self):
        _logger.info("Enabling")
        core.enabled = True
        ProfilerController.player_state = 'profiler_player_enabled'

    @http.route(['/web/profiler/disable'], type='json', auth="user")
    def disable(self, **post):
        _logger.info("Disabling")
        core.enabled = False
        ProfilerController.player_state = 'profiler_player_disabled'

    @http.route(['/web/profiler/clear'], type='json', auth="user")
    # @http.jsonrequest
    def clear(self, **post):
        core.profile.clear()
        _logger.info("Cleared stats")
        ProfilerController.player_state = 'profiler_player_clear'

    # @http.httprequest
    @http.route(['/web/profiler/dump'], type='http', auth="user")
    def dump(self, token, **post):
        """Provide the stats as a file download.

        Uses a temporary file, because apparently there's no API to
        dump stats in a stream directly.
        """
        exclude_fname = [os.path.expanduser(path) for path in request.env.ref(
            'profiler.default_exclude_fnames_pstas',
            raise_if_not_found=False).value.split(',')]
        # exclude_query = request.env.ref(
        #     'profiler.default_exclude_query_pgbader',
        #     raise_if_not_found=False).value.split(',')
        with tools.osutil.tempdir() as dump_dir:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = 'openerp_%s' % ts
            stats_path = os.path.join(dump_dir, '%s.stats' % filename)
            core.profile.dump_stats(stats_path)
            pstats_list = get_pstats_print2list(
                stats_path, sort='cumulative', limit=45,
                exclude_fnames=exclude_fname)
            with Capturing() as output:
                print_pstats_list(pstats_list)
            handle = tempfile.mkstemp(
                suffix='.txt', prefix=filename, dir=dump_dir)[0]
            res_file = os.fdopen(handle, "a")
            for line in output:
                res_file.write('%s\n' % line)
            res_file.close()
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
            raise Exception("pgbadger not found")
        filename = os.path.join(dir_dump, output)
        logfilename = os.path.join(dir_dump, 'postgresql.log')
        # TODO: Get ths path from os.environ or somewhere
        log_path = '/var/lib/postgresql/9.5/main/pg_log/postgresql.log'
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:
                # error is different than File exists
                if exc.errno != errno.EEXIST:
                    raise
        shutil.copyfile(log_path, logfilename)
        _logger.info("Generating PG Badger report.")
        command = (
            '%s -f stderr -T "%s" -o %s --top 40 --sample 2 '
            '--disable-type --disable-error --disable-hourly '
            '--disable-session --disable-connection --disable-temporary '
            '--quiet %s' % (
                pgbadger, 'Odoo-Profiler', filename, log_path))
        _logger.info("Command:")
        _logger.info(command)
        subprocess.call(command, shell=True)
        _logger.info("Done")
