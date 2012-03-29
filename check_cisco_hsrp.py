#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
#===============================================================================
# Name          : check_cisco_hsrp.py
# Author        : Vincent BESANCON <besancon.vincent@gmail.com>
# Description   : Check HSRP on Cisco devices. Check if the router must be the
#                 active or standby router for VLANs.
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

__version__ = '1.2.2'

import os, sys

from monitoring.nagios.plugin.snmp import NagiosPluginSNMP

# Specific class for this plugin
class CheckCiscoHSRP(NagiosPluginSNMP):
    def __init__(self, name, version, description):
        super(CheckCiscoHSRP, self).__init__(name, version, description)
        self.roleid = {'initial': 1, 'learn': 2, 'listen': 3, 'speak': 4, 'standby': 5, 'active': 6}
        self.rolename = {1: 'initial', 2: 'learn', 3: 'listen', 4: 'speak', 5: 'standby', 6: 'active'}

    def define_plugin_arguments(self):
        """Define arguments for the plugin"""
        # Define common arguments
        super(CheckCiscoHSRP, self).define_plugin_arguments()

        # Add extra arguments
        self.required_args.add_argument('-r', '--role', dest='role',
                                  choices=['active', 'standby'], help='Role of this router', required=True)

# The main procedure
if __name__ == '__main__':
    progname = os.path.basename(sys.argv[0])
    progdesc = 'Check HSRP on Cisco devices. Check if the router must be the active or standby router for VLANs.'

    plugin = CheckCiscoHSRP(progname, __version__, progdesc)

    oid_hsrp_states = '1.3.6.1.4.1.9.9.106.1.2.1.1.15'
    oid_if_descr = '1.3.6.1.2.1.2.2.1.2'

    hsrp_states = plugin.snmpnext(oid_hsrp_states)

    # Checking state of HSRP for all interfaces
    longoutput = ""
    output = ""
    exit_code = 0
    nbr_error = 0
    for state in hsrp_states:
        ifIndex = state[0][-2]
        ifDescr = plugin.snmpget('%s.%s' % (oid_if_descr, ifIndex))

        if state[1] != plugin.roleid[plugin.options.role]:
            longoutput += '** %s is in state %s (must be %s) **\n' % (
            ifDescr[1], plugin.rolename[state[1]], plugin.options.role)
            nbr_error += 1
            exit_code = 1
        else:
            longoutput += '%s is in state %s\n' % (ifDescr[1], plugin.options.role)

    longoutput = longoutput.rstrip('\n')
    if exit_code == 1:
        output = '%d HRSP interface error !\n' % nbr_error
        plugin.warning(output + longoutput)
    elif not exit_code:
        output = 'Role for HSRP is %s.\n' % plugin.options.role
        plugin.ok(output + longoutput)
