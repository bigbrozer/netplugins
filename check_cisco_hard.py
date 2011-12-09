#!/usr/local/bin/python2.6
# -*- coding: UTF-8 -*-
#
#===============================================================================
# Name          : check_cisco_hard.py
# Author        : Vincent BESANCON aka 'v!nZ' <elguapito@free.fr>
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

        oid_sensor_names_table = '1.3.6.1.2.1.47.1.1.1.1.7'         # from ENTITY-MIB
        oid_sensors_status_table = '1.3.6.1.4.1.9.9.91.1.1.1.1.5'   # from CISCO-ENTITY-SENSOR-MIB

        sensor_status_table = plugin.queryNextSnmpOid(oid_sensors_status_table)

        longoutput = ""
        output = ""
        exit_code = 0
        nbr_sensor_fails = 0
        for sensor in sensor_status_table:
            sensor_index = sensor[0][-1]
            sensor_name = plugin.querySnmpOid('%s.%s' % (oid_sensor_names_table, sensor_index))

            # Sensor are in errors if >1 (ok(1), unavailable(2), nonoperational(3))
            # Skip sensors marked as unavailable
            if sensor[1] != 1 and sensor[1] != 2:
                longoutput += '** %s: Non operational ! **\n' % sensor_name[1]
                if exit_code != 2: exit_code = 1
                nbr_sensor_fails += 1
            else:
                longoutput += '%s: ok\n' % sensor_name[1]

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
