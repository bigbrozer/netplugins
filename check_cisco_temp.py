#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
#===============================================================================
# Name          : check_cisco_temp.py
# Author        : Vincent BESANCON <besancon.vincent@gmail.com>
# Description   : Check all temperature on Cisco devices and alert if one is above thresholds.
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
        """Define arguments for the plugin"""
        # Define common arguments
        super(CheckCiscoTEMP, self).setPluginArguments()

        # Add extra arguments
        self.argparser.add_option('-w', action='store', type="int", dest='warnthr',
                                  help='Warning threshold in percent (eg. 80)')
        self.argparser.add_option('-c', action='store', type="int", dest='critthr',
                                  help='Critical threshold in percent (eg. 90)')

    def checkPluginArguments(self):
        """Check syntax of all arguments"""
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

        # OIDs
        oid_sensor_types = '1.3.6.1.4.1.9.9.91.1.1.1.1.1'   # From CISCO-ENTITY-SENSOR-MIB
        oid_sensor_values = '1.3.6.1.4.1.9.9.91.1.1.1.1.4'  # From CISCO-ENTITY-SENSOR-MIB
        oid_entity_names = '1.3.6.1.2.1.47.1.1.1.1.7'       # From ENTITY-MIB

        # Store temp data
        temp_data = []
        
        # Get all "celsius" sensor types
        sensor_types = plugin.queryNextSnmpOid(oid_sensor_types)
        if sensor_types:
            for type in sensor_types:
                plugin.debug('Sensor type is: %s' % type[1])

                # If sensor type is celsius(8)
                if type[1] == 8:
                    sensor_index = type[0][-1]
                    sensor_name = plugin.querySnmpOid('%s.%s' % (oid_entity_names, sensor_index))
                    sensor_value = plugin.querySnmpOid('%s.%s' % (oid_sensor_values, sensor_index))
                    temp_data.append((sensor_name[1], sensor_value[1]))
                else:
                    plugin.debug('Skipping sensor type: %s' % type[1])
        else:
            plugin.unknown('SNMP Query Error: query all sensor types returned no result !')

        plugin.debug('Temp data: %s' % temp_data)
        
        # Check thresholds and format output to Nagios
        longoutput = ""
        longoutput_crit = ""
        longoutput_warn = ""
        longoutput_ok = ""
        output = ""
        perfdata = "| "
        exit_code = 0
        nbr_error = 0
        nbr_crit = 0
        nbr_warn = 0
        nbr_ok = 0
        for temp in temp_data:
            temp_descr, temp_value = temp
            
            if plugin.params.warnthr < temp_value < plugin.params.critthr:
                longoutput_warn += ' * %s: %d C (>%d) *\n' % (temp_descr, temp_value, plugin.params.warnthr)
                if exit_code != 2: exit_code = 1
                nbr_error += 1
                nbr_warn += 1
            elif temp_value > plugin.params.critthr:
                longoutput_crit += ' ** %s: %d C (>%d) **\n' % (temp_descr, temp_value, plugin.params.critthr)
                exit_code = 2
                nbr_error += 1
                nbr_crit += 1
            elif temp_value < plugin.params.warnthr:
                longoutput_ok += ' %s: %d C (<%d)\n' % (temp_descr, temp_value, plugin.params.warnthr)
                nbr_ok += 1

            perfdata += '%s=%dC;%d;%d;; ' % (
                str(temp_descr).replace(' ', '_').replace(',', '_').replace('_temperature', ''),
                temp_value,
                plugin.params.warnthr,
                plugin.params.critthr
            )

        # Format output
        if nbr_crit > 0:
            longoutput += 'Critical: (%d)\n%s\n' % (nbr_crit, longoutput_crit)
        if nbr_warn > 0:
            longoutput += 'Warning: (%d)\n%s\n' % (nbr_warn, longoutput_warn)
        if nbr_ok > 0:
            longoutput += 'OK: (%d)\n%s\n' % (nbr_ok, longoutput_ok)

        # Add perfdata
        longoutput += perfdata

        # Output to Nagios
        longoutput = longoutput.rstrip('\n')
        if exit_code == 2:
            output = '%d temperature sensor above thresholds !\n' % nbr_error
            plugin.critical(output + longoutput)
        elif exit_code == 1:
            output = '%d temperature sensor above thresholds !\n' % nbr_error
            plugin.warning(output + longoutput)
        elif not exit_code:
            output = 'All temperature sensor are below thresholds.\n'
            plugin.ok(output + longoutput)
    except Exception as e:
        print "Arrrgh... exception occured ! Please contact DL-ITOP-MONITORING."
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
        raise SystemExit(3)
