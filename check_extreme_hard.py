#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
#===============================================================================
# Name          : check_extreme_hard.py
# Author        : Vincent BESANCON <besancon.vincent@gmail.com>
# Description   : Check hardware (power only) of Extreme devices.
#-------------------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#===============================================================================
#
#

__version__ = '1.2'

import os, sys

from monitoring.nagios.plugin.snmp import NagiosPluginSNMP

# Specific class for this plugin
class CheckExtremeHard(NagiosPluginSNMP):
    def __init__(self, name, version, description):
        super(CheckExtremeHard, self).__init__(name, version, description)
        # 1normal,2warning,3critical,4shutdown,5notPresent,6notFunctioning
        self.statusname = {1: 'Not present', 2: 'Normal', 3: 'Error'}

    def define_plugin_arguments(self):
        """Define arguments for the plugin"""
        # Define common arguments
        super(CheckExtremeHard, self).define_plugin_arguments()

        # Add extra arguments
        self.required_args.add_argument('-T', '--type', choices=['power'], dest='type',
                                  help='Type of hardware to check.', required=True)

# The main procedure
if __name__ == '__main__':
    progname = os.path.basename(sys.argv[0])
    progdesc = 'Check hardware (power only) of Extreme devices.'

    plugin = CheckExtremeHard(progname, __version__, progdesc)

    oid_powers_status = '1.3.6.1.4.1.1916.1.1.1.27.1.2'
    oid_hard_status = oid_powers_status

    hard_status = plugin.snmpnext(oid_hard_status)

    # Checking state of hardware
    longoutput = ""
    output = ""
    exit_code = 0
    nbr_error = 0
    i = 0
    for power in hard_status:
        state_code = power[1]
        power_name = 'Power%d' % i

        if state_code != 2:
            longoutput += '** %s: %s **\n' % (power_name, plugin.statusname[state_code])
            nbr_error += 1
            exit_code = 1
        else:
            longoutput += '%s: %s\n' % (power_name, plugin.statusname[state_code])
        i += 1

    # Formatting output
    longoutput = longoutput.rstrip('\n')
    if exit_code == 1:
        output = '%d %s health in error !\n' % (nbr_error, plugin.options.type.title())
        plugin.critical(output + longoutput)
    elif not exit_code:
        output = '%s health is good.\n' % plugin.options.type.title()
        plugin.ok(output + longoutput)
