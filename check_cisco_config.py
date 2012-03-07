#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
#===============================================================================
# Name          : check_cisco_config.py
# Authors       : Vincent BESANCON <besancon.vincent@gmail.com>
#                 Julien DORMOY aka Fusionwork <dormoyjuju@free.fr>
# Description   : Check config last change and last saved date time.
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
import os, sys, traceback
from time import strftime, localtime, time

try:
    from nagios.plugin.snmp import NagiosPluginSNMP
except Exception as e:
    print "Arrrgh... exception occured ! Please contact DL-ITOP-MONITORING."
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
    raise SystemExit(3)

# Specific class for this plugin
class CheckCiscoConfig(NagiosPluginSNMP):
    def __init__(self, name, version, description):
        super(CheckCiscoConfig, self).__init__(name, version, description)

    def setPluginArguments(self):
        """Define arguments for the plugin"""
        # Define common arguments
        super(CheckCiscoConfig, self).setPluginArguments()

        # Add extra arguments

    def checkPluginArguments(self):
        """Check syntax of all arguments"""
        # Check common arguments syntax
        super(CheckCiscoConfig, self).checkPluginArguments()

        # Check extra arguments syntax

# The main procedure
if __name__ == '__main__':
    try:
        progname = os.path.basename(sys.argv[0])
        progdesc = 'Check config last change and last saved date time.'
        progversion = '1.0'

        plugin = CheckCiscoConfig(progname, progversion, progdesc)

        oid_uptime = '1.3.6.1.2.1.1.3.0'
        oid_config_last_changed = '1.3.6.1.4.1.9.9.43.1.1.1.0'
        oid_config_last_saved = '1.3.6.1.4.1.9.9.43.1.1.2.0'

        uptime = plugin.querySnmpOid(oid_uptime)
        config_last_changed = plugin.querySnmpOid(oid_config_last_changed)
        config_last_saved = plugin.querySnmpOid(oid_config_last_saved)

        # Date calculations
        delta_time_changed = abs(long(uptime[1]) - long(config_last_changed[1])) / 100
        delta_time_saved = abs(long(uptime[1]) - long(config_last_saved[1])) / 100

        config_last_changed_date = localtime(time() - delta_time_changed)
        config_last_changed_date_str = strftime('%d/%m/%Y %H:%M', config_last_changed_date)
        config_last_saved_date = localtime(time() - delta_time_saved)
        config_last_saved_date_str = strftime('%d/%m/%Y %H:%M', config_last_saved_date)

        # Formating output
        longoutput = 'Config last changed: %s\nConfig last saved: %s' % (
            config_last_changed_date_str,
            config_last_saved_date_str,
        )

        # Checking state of config date
        if config_last_changed_date > config_last_saved_date:
            output = 'Config was changed without saving on %s !\n' % config_last_changed_date_str
            plugin.warning(output + longoutput)
        else:
            output = 'Running configuration was saved on %s.\n' % config_last_saved_date_str
            plugin.ok(output + longoutput)
    except Exception as e:
        print "Arrrgh... exception occured ! Please contact DL-ITOP-MONITORING."
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
        raise SystemExit(3)
