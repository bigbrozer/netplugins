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
import logging as log
import os, sys

from monitoring.nagios.plugin.snmp import NagiosPluginSNMP

logger = log.getLogger('plugin')

# Specific class for this plugin
class CheckCiscoTEMP(NagiosPluginSNMP):
    def define_plugin_arguments(self):
        """Define arguments for the plugin"""
        # Define common arguments
        super(CheckCiscoTEMP, self).define_plugin_arguments()

        # Add extra arguments
        self.required_args.add_argument('-w', type=int, dest='warnthr',
                                  help='Warning threshold in percent (eg. 80)', required=True)
        self.required_args.add_argument('-c', type=int, dest='critthr',
                                  help='Critical threshold in percent (eg. 90)', required=True)

# The main procedure
if __name__ == '__main__':
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
    sensor_types = plugin.snmpnext(oid_sensor_types)
    if sensor_types:
        for type in sensor_types:
            logger.debug('Sensor type is: %s' % type[1])

            # If sensor type is celsius(8)
            if type[1] == 8:
                sensor_index = type[0][-1]
                sensor_name = plugin.snmpget('%s.%s' % (oid_entity_names, sensor_index))
                sensor_value = plugin.snmpget('%s.%s' % (oid_sensor_values, sensor_index))
                temp_data.append((sensor_name[1], sensor_value[1]))
            else:
                logger.debug('Skipping sensor type: %s' % type[1])
    else:
        plugin.unknown('SNMP Query Error: query all sensor types returned no result !')

    logger.debug('Temp data: %s' % temp_data)

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

        if plugin.options.warnthr < temp_value < plugin.options.critthr:
            longoutput_warn += ' * %s: %d C (>%d) *\n' % (temp_descr, temp_value, plugin.options.warnthr)
            if exit_code != 2: exit_code = 1
            nbr_error += 1
            nbr_warn += 1
        elif temp_value > plugin.options.critthr:
            longoutput_crit += ' ** %s: %d C (>%d) **\n' % (temp_descr, temp_value, plugin.options.critthr)
            exit_code = 2
            nbr_error += 1
            nbr_crit += 1
        elif temp_value < plugin.options.warnthr:
            longoutput_ok += ' %s: %d C (<%d)\n' % (temp_descr, temp_value, plugin.options.warnthr)
            nbr_ok += 1

        perfdata += '%s=%dC;%d;%d;; ' % (
            str(temp_descr).replace(' ', '_').replace(',', '_').replace('_temperature', ''),
            temp_value,
            plugin.options.warnthr,
            plugin.options.critthr
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
