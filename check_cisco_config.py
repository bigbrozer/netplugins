#!/usr/local/bin/python2.6 -O
# -*- coding: UTF-8 -*-
#
#===============================================================================
# Name          : check_cisco_config.py
# Authors       : Vincent BESANCON aka 'v!nZ' <elguapito@free.fr>
#                 Julien DORMOY aka Fusionwork <dormoyjuju@free.fr>
# Version       : $Revision$
# Last Modified : $Date$
# License       : Creative Commons Attribution-Noncommercial-Share Alike 2.0 France
# Description   : Check config last change and last saved date time.
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
import os, sys
from time import strftime, localtime, time

sys.path.append("/usr/local/nagios/libexec/python")

from nagios.plugin.snmp import NagiosPluginSNMP

# Specific class for this plugin
class CheckCiscoConfig(NagiosPluginSNMP):
    def __init__(self, name, version, description):
        super(CheckCiscoConfig, self).__init__(name, version, description)
        
    def setPluginArguments(self):
        '''Define arguments for the plugin'''
        # Define common arguments
        super(CheckCiscoConfig, self).setPluginArguments()
        
        # Add extra arguments

    def checkPluginArguments(self):
        '''Check syntax of all arguments'''
        # Check common arguments syntax
        super(CheckCiscoConfig, self).checkPluginArguments()
        
        # Check extra arguments syntax

# The main procedure
if __name__ == '__main__':
    progname = os.path.basename(sys.argv[0])
    progdesc = 'Check config last change and last saved date time.'
    progversion = '$Revision: 1 $'
    
    plugin = CheckCiscoConfig(progname, progversion, progdesc)
    
    oid_uptime = '1.3.6.1.2.1.1.3.0'
    oid_config_last_changed = '1.3.6.1.4.1.9.9.43.1.1.1.0'
    oid_config_last_saved = '1.3.6.1.4.1.9.9.43.1.1.2.0'

    uptime = plugin.querySnmpOid(oid_uptime)
    config_last_changed = plugin.querySnmpOid(oid_config_last_changed)
    config_last_saved = plugin.querySnmpOid(oid_config_last_saved)
    
    # Date calculations
    delta_time_changed = (long(uptime[1]) - long(config_last_changed[1])) / 100
    delta_time_saved = (long(uptime[1]) - long(config_last_saved[1])) / 100
    
    config_last_changed_date = strftime('%d/%m/%Y %H:%M', localtime(time()-delta_time_changed))
    config_last_saved_date = strftime('%d/%m/%Y %H:%M', localtime(time()-delta_time_saved))
    
    # Formating output
    longoutput = 'Config last changed: %s\nConfig last saved: %s' % (config_last_changed_date, config_last_saved_date)
    
    # Checking state of config date
    if config_last_changed[1] > config_last_saved[1]:
        output = 'Config was changed without saving on %s !\n' % config_last_changed_date
        plugin.warning(output + longoutput)
    else:
        output = 'Running configuration was saved on %s.\n' % config_last_saved_date
        plugin.ok(output + longoutput)
