#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
#===============================================================================
# Name          : check_cisco_hard.py
# Author        : Vincent BESANCON <besancon.vincent@gmail.com>
# Description   : Check hardware (sensors, fans, power) of Cisco devices.
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

import shared
from monitoring.nagios.plugin.snmp import NagiosPluginSNMP
from monitoring.utils.snmp import convert_tuple_to_oid

logger = log.getLogger('plugin')

# The main procedure
if __name__ == '__main__':
    progname = os.path.basename(sys.argv[0])
    progdesc = 'Check hardware (sensors, fans, power) of Cisco devices.'

    plugin = NagiosPluginSNMP(progname, shared.__version__, progdesc)

    # OIDs for devices supporting CISCO-ENTITY-SENSOR-MIB
    oid_sensor_names_table = '1.3.6.1.2.1.47.1.1.1.1.7'         # from ENTITY-MIB
    oid_sensors_status_table = '1.3.6.1.4.1.9.9.91.1.1.1.1.5'   # from CISCO-ENTITY-SENSOR-MIB

    # OIDs for devices supporting CISCO-ENVMON-MIB
    oid_envmon_fan_status_table = '1.3.6.1.4.1.9.9.13.1.4.1'      # from CISCO-ENVMON-MIB
    oid_envmon_power_status_table = '1.3.6.1.4.1.9.9.13.1.5.1'    # from CISCO-ENVMON-MIB

    oid_envmon_fan_status = '%s.3' % oid_envmon_fan_status_table
    oid_envmon_power_status = '%s.3' % oid_envmon_power_status_table

    # Store all sensors data
    sensor_data = []

    # Query using CISCO-ENTITY-SENSOR-MIB be default, fallback to CISCO-ENVMON-MIB
    sensor_status_list = plugin.snmpnext(oid_sensors_status_table)
    if not sensor_status_list:
        # Does not support CISCO-ENTITY-SENSOR-MIB
        logger.debug('Device not supporting CISCO-ENTITY-SENSOR-MIB, fallback.')
        sensor_status_list = plugin.snmpnext(oid_envmon_fan_status)
        sensor_status_list.extend(plugin.snmpnext(oid_envmon_power_status))

        for sensor in sensor_status_list:
            sensor_index = sensor[0][-1]
            sensor_name = plugin.snmpget('%s.2.%s' % (convert_tuple_to_oid(sensor[0][0:12]), sensor_index))[1]
            sensor_status = sensor[1]

            # Skip sensor status marked as unavailable(2)
            if sensor_status == 5:
                continue

            sensor_data.append((sensor_name, sensor_status))
    else:
        # Support CISCO-ENTITY-SENSOR-MIB
        logger.debug('Device supporting CISCO-ENTITY-SENSOR-MIB, continue.')
        for sensor in sensor_status_list:
            sensor_index = sensor[0][-1]
            sensor_name = plugin.snmpget('%s.%s' % (oid_sensor_names_table, sensor_index))[1]
            sensor_status = sensor[1]

            # Skip sensor status marked as unavailable(2)
            if sensor_status == 2:
                continue

            sensor_data.append((sensor_name, sensor_status))

    logger.debug('Sensor data:')
    logger.debug('\t%s' % sensor_data)

    # Return OK if no hardware sensor support is available
    if not len(sensor_data):
        plugin.ok('No support for hardware sensor available.')

    # Check thresholds and format output to Nagios
    longoutput = ""
    output = ""
    exit_code = 0
    nbr_sensor_fails = 0
    for sensor in sensor_data:
        sensor_name, sensor_status = sensor

        # Sensor are in errors if >1
        if sensor_status > 1:
            longoutput += '** %s: Non operational ! **\n' % sensor_name
            if exit_code != 2: exit_code = 1
            nbr_sensor_fails += 1
        else:
            longoutput += '%s: ok\n' % sensor_name

    longoutput = longoutput.rstrip('\n')
    if exit_code == 1:
        output = '%d sensors are non operationals !\n' % nbr_sensor_fails
        plugin.critical(output + longoutput)
    elif not exit_code:
        output = 'Sensor health is good.\n'
        plugin.ok(output + longoutput)
