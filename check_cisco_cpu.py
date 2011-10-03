#!/usr/local/bin/python2.6 -O
# -*- coding: UTF-8 -*-
#
#===============================================================================
# Name          : check_cisco_cpu.py
# Author        : Vincent BESANCON aka 'v!nZ' <elguapito@free.fr>
# Version       : $Revision$
# Last Modified : $Date$
# License       : Creative Commons Attribution-Noncommercial-Share Alike 2.0 France
# Description   : Check all CPUs usage on Cisco devices supporting CISCO-PROCESS-MIB.
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
class CheckCiscoCPU(NagiosPluginSNMP):
    def __init__(self, name, version, description):
        super(CheckCiscoCPU, self).__init__(name, version, description)
        
    def setPluginArguments(self):
        '''Define arguments for the plugin'''
        # Define common arguments
        super(CheckCiscoCPU, self).setPluginArguments()
        
        # Add extra arguments
        self.argparser.add_option('-w', action='store', type="int", dest='warnthr', help='Warning threshold in percent (eg. 80)')
        self.argparser.add_option('-c', action='store', type="int", dest='critthr', help='Critical threshold in percent (eg. 90)')

    def checkPluginArguments(self):
        '''Check syntax of all arguments'''
        # Check common arguments syntax
        super(CheckCiscoCPU, self).checkPluginArguments()
        
        # Check extra arguments syntax
        if not self.params.warnthr or not self.params.critthr:
            self.unknown('Missing thresholds ! (options -w and -c)')

# The main procedure
if __name__ == '__main__':
    try:
        progname = os.path.basename(sys.argv[0])
        progdesc = 'Check all CPUs usage on Cisco devices supporting CISCO-PROCESS-MIB.'
        progversion = '$Revision: 1 $'

        plugin = CheckCiscoCPU(progname, progversion, progdesc)

        oid_entity_name = '1.3.6.1.2.1.47.1.1.1.1.7'
        oid_cpu_indexes = '1.3.6.1.4.1.9.9.109.1.1.1.1.2'
        oid_cpu_usages = '1.3.6.1.4.1.9.9.109.1.1.1.1.8'

        cpu_indexes = plugin.queryNextSnmpOid(oid_cpu_indexes)
        cpu_usages = plugin.queryNextSnmpOid(oid_cpu_usages)

        cpu_data = {}
        for i in range(0, len(cpu_indexes)):
            cpu_name = str(plugin.querySnmpOid('%s.%s' % (oid_entity_name, cpu_indexes[i][1]))[1])

            # Test if there is a description, if not generate one
            if len(cpu_name) == 0:
                cpu_name = 'CPU%d' % i

            cpu_data[cpu_name] = int(cpu_usages[i][1])


        # Checking values if in thresholds and formatting output
        output = ""
        longoutput = ""
        exit_code = 0
        nbr_error = 0
        i = 1
        for cpu in cpu_data:
            if plugin.params.warnthr < cpu_data[cpu] < plugin.params.critthr:
                longoutput += '* %s: %d%% * (>%d)\n' % (cpu, cpu_data[cpu], plugin.params.warnthr)
                if exit_code != 2: exit_code = 1
                nbr_error+=1
            elif cpu_data[cpu] > plugin.params.critthr:
                longoutput += '** %s: %d%% ** (>%d)\n' % (cpu, cpu_data[cpu], plugin.params.critthr)
                exit_code = 2
                nbr_error+=1
            elif cpu_data[cpu] < plugin.params.warnthr:
                longoutput += '%s: %d%% (<%d)\n' % (cpu, cpu_data[cpu], plugin.params.warnthr)

        # Formatting perfdata
        perfdata = " | "
        for cpu in cpu_data:
            perfdata += '%s=%d%%;%d;%d;0;100 ' % (cpu.replace(' ', '_'), cpu_data[cpu], plugin.params.warnthr, plugin.params.critthr)

        # Output to Nagios
        longoutput = longoutput.rstrip('\n')
        if exit_code == 0:
            output = 'All CPU usage are below thresholds.\n'
            longoutput += perfdata
            plugin.ok(output + longoutput)
        elif exit_code == 1:
            output = '%d CPU are above %d%% of usage !\n' % (nbr_error, plugin.params.warnthr)
            longoutput += perfdata
            plugin.warning(output + longoutput)
        elif exit_code == 2:
            output = '%d CPU are above %d%% of usage !\n' % (nbr_error, plugin.params.critthr)
            longoutput += perfdata
            plugin.critical(output + longoutput)
    except Exception as e:
        print "Arrrgh... exception occured ! Please contact DL-ITOP-MONITORING."
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
        raise SystemExit(3)
