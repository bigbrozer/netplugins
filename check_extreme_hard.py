#!/usr/local/bin/python2.6 -O
# -*- coding: UTF-8 -*-
#
#===============================================================================
# Name          : check_extreme_hard.py
# Author        : Vincent BESANCON aka 'v!nZ' <elguapito@free.fr>
# Version       : $Revision$
# Last Modified : $Date$
# License       : Creative Commons Attribution-Noncommercial-Share Alike 2.0 France
# Description   : Check hardware (power only) of Extreme devices.
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
import os, sys

from nagios.plugin.snmp import NagiosPluginSNMP

# Specific class for this plugin
class CheckExtremeAlim(NagiosPluginSNMP):
    def __init__(self, name, version, description):
        super(CheckExtremeAlim, self).__init__(name, version, description)
        # 1normal,2warning,3critical,4shutdown,5notPresent,6notFunctioning
        self.statusname = {1: 'Not present', 2: 'Normal', 3: 'Error'}
        
    def setPluginArguments(self):
        '''Define arguments for the plugin'''
        # Define common arguments
        super(CheckExtremeAlim, self).setPluginArguments()
        
        # Add extra arguments
        self.argparser.add_option('-T', '--type', action='store', type="choice", choices=['power'], dest='type', help='Type of hardware to check (choices: power)')

    def checkPluginArguments(self):
        '''Check syntax of all arguments'''
        # Check common arguments syntax
        super(CheckExtremeAlim, self).checkPluginArguments()
        
        # Check extra arguments syntax
        if not self.params.type:
            self.unknown('Missing type of hardware to check for ! (options -T or --type)')

# The main procedure
if __name__ == '__main__':
    progname = os.path.basename(sys.argv[0])
    progdesc = 'Check hardware (power only) of Extreme devices.'
    progversion = '$Revision: 1 $'
    
    plugin = CheckExtremeAlim(progname, progversion, progdesc)
    
    oid_powers_status = '1.3.6.1.4.1.1916.1.1.1.27.1.2'

    if plugin.params.type == 'power':    
        oid_hard_status = oid_powers_status

    hard_status = plugin.queryNextSnmpOid(oid_hard_status)
    
    # Checking state of hardware
    longoutput = ""
    output = ""
    exit_code = 0
    nbr_error = 0
    i = 0
    for power in hard_status:
        state_code = power[1]
        power_name = 'Power%d' % i

        if state_code != 2:
            longoutput += '** %s: %s **\n' % (power_name, plugin.statusname[state_code])
            nbr_error+=1
            exit_code = 1
        else:
            longoutput += '%s: %s\n' % (power_name, plugin.statusname[state_code])
        i+=1

    # Formatting output
    longoutput = longoutput.rstrip('\n')
    if exit_code == 1:
        output = '%d %s health in error !\n' % (nbr_error, plugin.params.type.title())
        plugin.critical(output + longoutput)
    elif exit_code == 0:
        output = '%s health is good.\n' % plugin.params.type.title()
        plugin.ok(output + longoutput)
