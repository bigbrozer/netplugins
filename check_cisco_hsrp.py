#!/usr/local/bin/python2.6
# -*- coding: UTF-8 -*-
#
#===============================================================================
# Name          : check_cisco_hsrp.py
# Author        : Vincent BESANCON aka 'v!nZ' <elguapito@free.fr>
# License       : Creative Commons Attribution-Noncommercial-Share Alike 2.0 France
# Description   : Check HSRP on Cisco devices. Check if the router must be the
#                 active or standby router for VLANs.
#-------------------------------------------------------------------------------
# This work is licensed under the 
# Creative Commons Attribution-Noncommercial-Share Alike 2.0 France License.
# To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/2.0/fr/ or send a letter to
#
# Creative Commons
# 171 Second Street, Suite 300
# San Francisco, California
# 94105, USA.
#===============================================================================

import os, sys, traceback

try:
    from nagios.plugin.snmp import NagiosPluginSNMP
except Exception as e:
    print "Arrrgh... exception occured ! Please contact DL-ITOP-MONITORING."
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
    raise SystemExit(3)

# Specific class for this plugin
class CheckCiscoHSRP(NagiosPluginSNMP):
    def __init__(self, name, version, description):
        super(CheckCiscoHSRP, self).__init__(name, version, description)
        self.roleid = {'initial': 1, 'learn': 2, 'listen': 3, 'speak': 4, 'standby': 5, 'active': 6}
        self.rolename = {1: 'initial', 2: 'learn', 3: 'listen', 4: 'speak', 5: 'standby', 6: 'active'}

    def setPluginArguments(self):
        '''Define arguments for the plugin'''
        # Define common arguments
        super(CheckCiscoHSRP, self).setPluginArguments()

        # Add extra arguments
        self.argparser.add_option('-r', '--role', action='store', type='choice', dest='role',
                                  choices=['active', 'standby'], help='Role of this router')

    def checkPluginArguments(self):
        '''Check syntax of all arguments'''
        # Check common arguments syntax
        super(CheckCiscoHSRP, self).checkPluginArguments()

        # Check extra arguments syntax
        if not self.params.role:
            self.unknown('Missing role ! (options -r or --role)')

# The main procedure
if __name__ == '__main__':
    try:
        progname = os.path.basename(sys.argv[0])
        progdesc = 'Check HSRP on Cisco devices. Check if the router must be the active or standby router for VLANs.'
        progversion = '$Revision: 1 $'

        plugin = CheckCiscoHSRP(progname, progversion, progdesc)

        oid_hsrp_states = '1.3.6.1.4.1.9.9.106.1.2.1.1.15'
        oid_if_descr = '1.3.6.1.2.1.2.2.1.2'

        hsrp_states = plugin.queryNextSnmpOid(oid_hsrp_states)

        # Checking state of HSRP for all interfaces
        longoutput = ""
        output = ""
        exit_code = 0
        nbr_error = 0
        for state in hsrp_states:
            ifIndex = state[0][-2]
            ifDescr = plugin.querySnmpOid('%s.%s' % (oid_if_descr, ifIndex))

            if state[1] != plugin.roleid[plugin.params.role]:
                longoutput += '** %s is in state %s (must be %s) **\n' % (
                ifDescr[1], plugin.rolename[state[1]], plugin.params.role)
                nbr_error += 1
                exit_code = 1
            else:
                longoutput += '%s is in state %s\n' % (ifDescr[1], plugin.params.role)

        longoutput = longoutput.rstrip('\n')
        if exit_code == 1:
            output = '%d HRSP interface error !\n' % nbr_error
            plugin.warning(output + longoutput)
        elif exit_code == 0:
            output = 'Role for HSRP is %s.\n' % plugin.params.role
            plugin.ok(output + longoutput)
    except Exception as e:
        print "Arrrgh... exception occured ! Please contact DL-ITOP-MONITORING."
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
        raise SystemExit(3)
