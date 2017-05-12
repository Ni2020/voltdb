# This file is part of VoltDB.
# Copyright (C) 2008-2017 VoltDB Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with VoltDB.  If not, see <http://www.gnu.org/licenses/>.
import sys
from voltcli import checkstats
from voltcli.checkstats import StatisticsProcedureException

def reset(runner):
    result = runner.call_proc('@ResetDR', [VOLT.FastSerializer.VOLTTYPE_TINYINT, VOLT.FastSerializer.VOLTTYPE_TINYINT, VOLT.FastSerializer.VOLTTYPE_TINYINT],
                              [runner.opts.clusterId, runner.opts.forcing * 1, runner.opts.resetAll * 1 - runner.opts.resetSelf * 1]).table(0)
    status = result.tuple(0).column_integer(0)
    message = result.tuple(0).column_string(1)
    if status == 0:
        runner.info(message)
    else:
        runner.error(message)
        sys.exit(1)

    # post check for resetSelf
    if runner.opts.resetSelf:
        actionMessage = 'Not all connected clusters report received reset. You may continue monitoring remaining consumer clusters with @Statistics'
        try:
            checkstats.check_no_dr_consumer(runner)
        except StatisticsProcedureException as proex:
            runner.info('The previous command has timed out and stopped waiting... The cluster is in resetting DR phase.')
            runner.error(proex.message)
            if proex.isTimeout:
                runner.info(actionMessage)
            sys.exit(proex.exitCode)
        except (KeyboardInterrupt, SystemExit):
            runner.info('The previous command has stopped waiting... The cluster is in resetting DR phase.')
            runner.abort(actionMessage)

@VOLT.Multi_Command(
    bundles = VOLT.AdminBundle(),
    description = 'DR control command.',
    options = (
            VOLT.BooleanOption('-f', '--force', 'forcing', 'bypass precheck', default = False),
            VOLT.IntegerOption('-c', '--cluster', 'clusterId', 'cluster ID', default = -1),
            VOLT.BooleanOption('-a', '--all', 'resetAll', 'reset all connected cluster(s)', default = False),
            VOLT.BooleanOption('-s', '--self', 'resetSelf', 'gracefully reset self', default = False),
            VOLT.IntegerOption('-t', '--timeout', 'timeout', 'The timeout value in seconds if @Statistics is not progressing.', default = 0),
    ),
    modifiers = (
            VOLT.Modifier('reset', reset, 'reset one/all remote dr cluster(s).'),
    )
)

def dr(runner):
    if runner.opts.forcing and runner.opts.resetAll:
        runner.abort_with_help('You cannot specify both --force and --all options.')
    if runner.opts.clusterId >= 0 and runner.opts.resetAll:
        runner.abort_with_help('You cannot specify both --cluster and --all options.')
    if runner.opts.clusterId >= 0 and runner.opts.resetSelf:
        runner.abort_with_help('You cannot specify both --cluster and --self options.')
    if runner.opts.resetAll and runner.opts.resetSelf:
        runner.abort_with_help('You cannot specify both --all and --self options.')
    if runner.opts.clusterId < -1 or runner.opts.clusterId > 127:
        runner.abort_with_help('The cluster ID must be in the range of 0 to 127.')
    if runner.opts.timeout < 0:
        runner.abort_with_help('The timeout value must be more than zero seconds.')
    runner.go()
