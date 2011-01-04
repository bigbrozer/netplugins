#!/usr/local/bin/python2.6
# -*- coding: UTF-8 -*-
#
#===============================================================================
# Name          : check_cisco_hard.py
# Author        : Vincent BESANCON aka 'v!nZ' <elguapito@free.fr>
# Version       : $Revision$
# Last Modified : $Date$
# License       : Creative Commons Attribution-Noncommercial-Share Alike 2.0 France
# Description   : Check hardware (sensors, fans, power) of Cisco devices.
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
#
#
import os, sys, traceback

from nagios.plugin.snmp import NagiosPluginSNMP

# Specific class for this plugin
class CheckCiscoHard(NagiosPluginSNMP):
    def __init__(self, name, version, description):
        super(CheckCiscoHard, self).__init__(name, version, description)
        # 1normal,2warning,3critical,4shutdown,5notPresent,6notFunctioning
        self.statusname = {1: 'Normal', 2: 'Warning', 3: 'Critical', 4: 'Shutdown', 5: 'Not present', 6: 'Not functioning'}
        
    def setPluginArguments(self):
        '''Define arguments for the plugin'''
        # Define common arguments
        super(CheckCiscoHard, self).setPluginArguments()
        
        # Add extra arguments
        self.argparser.add_option('-T', '--type', action='store', type="choice", choices=['sensor','fan','power'], dest='type', help='Type of hardware to check (thermal, fan or power)')

    def checkPluginArguments(self):
        '''Check syntax of all arguments'''
        # Check common arguments syntax
        super(CheckCiscoHard, self).checkPluginArguments()
        
        # Check extra arguments syntax
        if not self.params.type:
            self.unknown('Missing type of hardware to check for ! (options -T or --type)')

# The main procedure
if __name__ == '__main__':
    try:
        progname = os.path.basename(sys.argv[0])
        progdesc = 'Check hardware (sensors, fans, power) of Cisco devices.'
        progversion = '$Revision: 1 $'

        plugin = CheckCiscoHard(progname, progversion, progdesc)

        oid_sensors_names = '1.3.6.1.4.1.9.9.13.1.3.1.2'
        oid_fans_names = '1.3.6.1.4.1.9.9.13.1.4.1.2'
        oid_powers_names = '1.3.6.1.4.1.9.9.13.1.5.1.2'

        oid_sensors_status = '1.3.6.1.4.1.9.9.13.1.3.1.6'
        oid_fans_status = '1.3.6.1.4.1.9.9.13.1.4.1.3'
        oid_powers_status = '1.3.6.1.4.1.9.9.13.1.5.1.3'

        if plugin.params.type == 'sensor':
            oid_hard_names = oid_sensors_names
            oid_hard_status = oid_sensors_status
        elif plugin.params.type == 'fan':
            oid_hard_names = oid_fans_names
            oid_hard_status = oid_fans_status
        elif plugin.params.type == 'power':
            oid_hard_names = oid_powers_names
            oid_hard_status = oid_powers_status

        hard_status = plugin.queryNextSnmpOid(oid_hard_status)

        # Checking state of HSRP for all interfaces
        longoutput = ""
        output = ""
        exit_code = 0
        nbr_error = 0
        for state in hard_status:
            stateIndex = state[0][-1]
            stateDescr = plugin.querySnmpOid('%s.%s' % (oid_hard_names, stateIndex))

            if state[1] > 1:
                longoutput += '** %s: %s **\n' % (stateDescr[1], plugin.statusname[1])
                if exit_code != 2: exit_code = 1
                nbr_error+=1
            else:
                longoutput += '%s: %s\n' % (stateDescr[1], plugin.statusname[1])

        longoutput = longoutput.rstrip('\n')
        if exit_code == 1:
            output = '%d %s in error !\n' % (nbr_error, plugin.params.type.title())
            plugin.critical(output + longoutput)
        elif exit_code == 0:
            output = '%s health is good.\n' % plugin.params.type.title()
            plugin.ok(output + longoutput)
    except Exception as e:
        print "Arrrgh... exception occured ! Please contact DL-ITOP-MONITORING."
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
        raise SystemExit(3)
