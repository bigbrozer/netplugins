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
import re
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
        self.required_args.add_argument('-w', nargs=3, metavar=('5k_outlet', 'fex_outlet', 'fex_die'), type=int, dest='warnthr',
                                  help='Warning threshold in percent for 5K Outlet, Fex Outlet and Fex Die.', required=True)
        self.required_args.add_argument('-c', nargs=3, metavar=('5k_outlet', 'fex_outlet', 'fex_die'), type=int, dest='critthr',
                                  help='Critical threshold in percent for 5K Outlet, Fex Outlet and Fex Die.', required=True)

# Function that verify thresholds
def check_thresholds(sensor, value, warn, crit):
    global count, perfdata, longoutput_warn, longoutput_crit, longoutput_ok
    global exit_code
    global nbr_error, nbr_warn, nbr_crit, nbr_ok

    if warn < value < crit:
        longoutput_warn += ' * %s: %d C (>%d <%d) *\n' % (sensor, value, warn, crit)
        if exit_code != 2: exit_code = 1
        nbr_error += 1
        nbr_warn += 1
    elif value > crit:
        longoutput_crit += ' ** %s: %d C (>%d) **\n' % (sensor, value, crit)
        exit_code = 2
        nbr_error += 1
        nbr_crit += 1
    elif value < warn:
        longoutput_ok += ' %s: %d C (<%d)\n' % (sensor, value, warn)
        nbr_ok += 1

    perfdata += '%d_%s=%dC;%d;%d;; ' % (
        count,
        sensor.replace(' ', '_').replace(',', '_').replace('_temperature', ''),
        value,
        warn,
        crit
    )

# The main procedure
if __name__ == '__main__':
    progname = os.path.basename(sys.argv[0])
    progdesc = 'Check all temperature on Cisco devices and alert if one is above thresholds.'
    progversion = '1.1'

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
                temp_data.append((str(sensor_name[1]), int(sensor_value[1])))
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
    count = 0

    # Expand tuple of thresholds
    outlet_warn, fexout_warn, fexdie_warn = plugin.options.warnthr
    outlet_crit, fexout_crit, fexdie_crit = plugin.options.critthr

    for temp in temp_data:
        count += 1
        temp_descr, temp_value = temp

        # Check 5K Outlet thresholds
        logger.debug('Processing sensor %s.' % temp_descr)
        if re.search(r'^Module.*Outlet', temp_descr):
            check_thresholds(temp_descr, temp_value, outlet_warn, outlet_crit)
        elif re.search(r'^Fex.*Outlet', temp_descr):
            check_thresholds(temp_descr, temp_value, fexout_warn, fexout_crit)
        elif re.search(r'^Fex.*Die', temp_descr):
            check_thresholds(temp_descr, temp_value, fexdie_warn, fexdie_crit)

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
