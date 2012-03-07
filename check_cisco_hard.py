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
import os, sys, traceback

try:
    from nagios.plugin.snmp import NagiosPluginSNMP
except Exception as e:
    print "Arrrgh... exception occured ! Please contact DL-ITOP-MONITORING."
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
    raise SystemExit(3)

# Specific class for this plugin
class CheckCiscoHard(NagiosPluginSNMP):
    def __init__(self, name, version, description):
        super(CheckCiscoHard, self).__init__(name, version, description)

# The main procedure
if __name__ == '__main__':
    try:
        progname = os.path.basename(sys.argv[0])
        progdesc = 'Check hardware (sensors, fans, power) of Cisco devices.'
        progversion = '1.2'

        plugin = CheckCiscoHard(progname, progversion, progdesc)

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
        sensor_status_list = plugin.queryNextSnmpOid(oid_sensors_status_table)
        if not sensor_status_list:
            # Does not support CISCO-ENTITY-SENSOR-MIB
            plugin.debug('Device not supporting CISCO-ENTITY-SENSOR-MIB, fallback.')
            sensor_status_list = plugin.queryNextSnmpOid(oid_envmon_fan_status)
            sensor_status_list.extend(plugin.queryNextSnmpOid(oid_envmon_power_status))

            for sensor in sensor_status_list:
                sensor_index = sensor[0][-1]
                sensor_name = plugin.querySnmpOid('%s.2.%s' % (plugin.tupleOidToDotted(sensor[0][0:12]), sensor_index))[1]
                sensor_status = sensor[1]

                # Skip sensor status marked as unavailable(2)
                if sensor_status == 5:
                    continue

                sensor_data.append((sensor_name, sensor_status))
        else:
            # Support CISCO-ENTITY-SENSOR-MIB
            plugin.debug('Device supporting CISCO-ENTITY-SENSOR-MIB, continue.')
            for sensor in sensor_status_list:
                sensor_index = sensor[0][-1]
                sensor_name = plugin.querySnmpOid('%s.%s' % (oid_sensor_names_table, sensor_index))[1]
                sensor_status = sensor[1]

                # Skip sensor status marked as unavailable(2)
                if sensor_status == 2:
                    continue
                
                sensor_data.append((sensor_name, sensor_status))

        plugin.debug('Sensor data:')
        plugin.debug('\t%s' % sensor_data)

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
        #noinspection PySimplifyBooleanCheck
        if exit_code == 1:
            output = '%d sensors are non operationals !\n' % nbr_sensor_fails
            plugin.critical(output + longoutput)
        elif exit_code == 0:
            output = 'Sensor health is good.\n'
            plugin.ok(output + longoutput)
    except Exception as e:
        print "Arrrgh... exception occured ! Please contact DL-ITOP-MONITORING."
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
        raise SystemExit(3)
