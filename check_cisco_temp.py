#!/usr/local/bin/python2.6 -O
# -*- coding: UTF-8 -*-
#
#===============================================================================
# Name          : check_cisco_temp.py
# Author        : Vincent BESANCON aka 'v!nZ' <elguapito@free.fr>
# License       : Creative Commons Attribution-Noncommercial-Share Alike 2.0 France
# Description   : Check all temperature on Cisco devices and alert if one is above thresholds.
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

try:
    from nagios.plugin.snmp import NagiosPluginSNMP
except Exception as e:
    print "Arrrgh... exception occured ! Please contact DL-ITOP-MONITORING."
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
    raise SystemExit(3)

# Specific class for this plugin
class CheckCiscoTEMP(NagiosPluginSNMP):
    def __init__(self, name, version, description):
        super(CheckCiscoTEMP, self).__init__(name, version, description)

    def setPluginArguments(self):
        """Define arguments for the plugin"""""
        # Define common arguments
        super(CheckCiscoTEMP, self).setPluginArguments()

        # Add extra arguments
        self.argparser.add_option('-w', action='store', type="int", dest='warnthr',
                                  help='Warning threshold in percent (eg. 80)')
        self.argparser.add_option('-c', action='store', type="int", dest='critthr',
                                  help='Critical threshold in percent (eg. 90)')

    def checkPluginArguments(self):
        """Check syntax of all arguments"""""
        # Check common arguments syntax
        super(CheckCiscoTEMP, self).checkPluginArguments()

        # Check extra arguments syntax
        if not self.params.warnthr or not self.params.critthr:
            self.unknown('Missing thresholds ! (options -w and -c)')

# The main procedure
if __name__ == '__main__':
    try:
        progname = os.path.basename(sys.argv[0])
        progdesc = 'Check all temperature on Cisco devices and alert if one is above thresholds.'
        progversion = '1.0'

        plugin = CheckCiscoTEMP(progname, progversion, progdesc)

        oid_temp_names = '1.3.6.1.4.1.9.9.13.1.3.1.2'
        oid_temp_values = '1.3.6.1.4.1.9.9.13.1.3.1.3'

        temp_values = plugin.queryNextSnmpOid(oid_temp_values)

        # Checking state of HSRP for all interfaces
        longoutput = ""
        output = ""
        perfdata = "| "
        exit_code = 0
        nbr_error = 0
        for temp in temp_values:
            tempIndex = temp[0][-1]
            tempDescr = plugin.querySnmpOid('%s.%s' % (oid_temp_names, tempIndex))

            if plugin.params.warnthr < temp[1] < plugin.params.critthr:
                longoutput += '* %s: %d C (>%d) *\n' % (tempDescr[1], temp[1], plugin.params.warnthr)
                if exit_code != 2: exit_code = 1
                nbr_error += 1
            elif temp[1] > plugin.params.critthr:
                longoutput += '** %s: %d C (>%d) **\n' % (tempDescr[1], temp[1], plugin.params.critthr)
                exit_code = 2
                nbr_error += 1
            elif temp[1] < plugin.params.warnthr:
                longoutput += '%s: %d C (<%d)\n' % (tempDescr[1], temp[1], plugin.params.warnthr)

            perfdata += '%s=%dC;%d;%d;; ' % (
            str(tempDescr[1]).replace(' ', '_').replace('_temperature', ''), temp[1], plugin.params.warnthr,
            plugin.params.critthr)

        # Add perfdata
        longoutput += perfdata

        # Output to Nagios
        longoutput = longoutput.rstrip('\n')
        #noinspection PySimplifyBooleanCheck
        if exit_code == 1:
            output = '%d temperature sensor above thresholds !\n' % nbr_error
            plugin.warning(output + longoutput)
        elif exit_code == 0:
            output = 'All temperature sensor are below thresholds.\n'
            plugin.ok(output + longoutput)
    except Exception as e:
        print "Arrrgh... exception occured ! Please contact DL-ITOP-MONITORING."
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
        raise SystemExit(3)
