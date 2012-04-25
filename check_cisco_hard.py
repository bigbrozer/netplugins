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

from shared import __version__
from monitoring.nagios.plugin import NagiosPluginSNMP

logger = log.getLogger('plugin')

# The main procedure
progname = os.path.basename(sys.argv[0])
progdesc = 'Check hardware (sensors, fans, power) of Cisco devices.'

plugin = NagiosPluginSNMP(version=__version__, description=progdesc)

oids = {
    # For devices supporting CISCO-ENTITY-SENSOR-MIB
    'sensor_names': '1.3.6.1.2.1.47.1.1.1.1.7',             # from ENTITY-MIB
    'sensors_status': '1.3.6.1.4.1.9.9.91.1.1.1.1.5',       # from CISCO-ENTITY-SENSOR-MIB
    # For devices supporting CISCO-ENVMON-MIB
    'envmon_fan_status': '1.3.6.1.4.1.9.9.13.1.4.1.3',      # from CISCO-ENVMON-MIB
    'envmon_power_status': '1.3.6.1.4.1.9.9.13.1.5.1.3',    # from CISCO-ENVMON-MIB
}

# Store all sensors data
sensor_data = []

# Query using CISCO-ENTITY-SENSOR-MIB be default, fallback to CISCO-ENVMON-MIB
query = plugin.snmp.getnext(oids)

# Return OK if no hardware sensor support is available
if not query.has_key('sensors_status') \
   and not query.has_key('envmon_fan_status') \
   and not query.has_key('envmon_power_status'):
    plugin.ok('No support for hardware sensor available.')

if not query.has_key('sensors_status'):
    # Does not support CISCO-ENTITY-SENSOR-MIB
    logger.debug('Device not supporting CISCO-ENTITY-SENSOR-MIB, fallback.')

    sensor_status = query['envmon_fan_status'] + query['envmon_power_status']
    for sensor in sensor_status:
        sensor_name = [e.pretty() for e in query['sensor_names'] if e.index == sensor.index][0]
        sensor_status = sensor.value

        # Skip sensor status marked as unavailable(2)
        if sensor_status == 5:
            continue

        sensor_data.append((sensor_name, sensor_status))
else:
    # Support CISCO-ENTITY-SENSOR-MIB
    logger.debug('Device supporting CISCO-ENTITY-SENSOR-MIB, continue.')
    sensor_status = query['sensors_status']
    for sensor in sensor_status:
        sensor_name = [e.pretty() for e in query['sensor_names'] if e.index == sensor.index][0]
        sensor_status = sensor.value

        # Skip sensor status marked as unavailable(2)
        if sensor_status == 2:
            continue

        sensor_data.append((sensor_name, sensor_status))

logger.debug('Sensor data:')
logger.debug('\t%s' % sensor_data)

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
