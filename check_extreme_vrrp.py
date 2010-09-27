#!/usr/local/bin/python2.6 -O
# -*- coding: UTF-8 -*-
#
#===============================================================================
# Name          : check_extreme_vrrp.py
# Authors       : Vincent BESANCON aka 'v!nZ' <elguapito@free.fr>
#                 Julien DORMOY aka Fusionwork <dormoyjuju@free.fr>
# Version       : $Revision: 417 $
# Last Modified : $Date: 2010-03-02 12:58:51 +0100 (mar., 02 mars 2010) $
# License       : Creative Commons Attribution-Noncommercial-Share Alike 2.0 France
# Description   : Check VRRP status of VLAN on Extreme Core devices.
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

sys.path.append("/usr/local/nagios/libexec/python")

from nagios.plugin.snmp import NagiosPluginSNMP

# Specific class for this plugin
class CheckExtremeVRRP(NagiosPluginSNMP):
    def __init__(self, name, version, description):
        super(CheckExtremeVRRP, self).__init__(name, version, description)
        self.vrrp_status = {1: 'initialize', 2: 'backup', 3: 'master'}
        
    def setPluginArguments(self):
        '''Define arguments for the plugin'''
        # Define common arguments
        super(CheckExtremeVRRP, self).setPluginArguments()
        
        # Add extra arguments
        self.argparser.add_option('-w', action='store', type="int", dest='warnthr', help='Warning threshold, sum of all vrrp status.')

    def checkPluginArguments(self):
        '''Check syntax of all arguments'''
        # Check common arguments syntax
        super(CheckExtremeVRRP, self).checkPluginArguments()
        
        # Check extra arguments syntax
        if not self.params.warnthr:
            self.unknown('Missing thresholds ! (options -w)')

# The main procedure
if __name__ == '__main__':
    progname = os.path.basename(sys.argv[0])
    progdesc = 'Check VRRP status of VLAN on Extreme Core devices.'
    progversion = '$Revision: 417 $'
    
    plugin = CheckExtremeVRRP(progname, progversion, progdesc)
    
    oid_vlan_names = '1.3.6.1.4.1.1916.1.2.8.1.1.1'         # Append vlan_id
    oid_vlan_interfaces = '1.3.6.1.4.1.1916.1.2.4.1.1.1'    # Provide vlan_id and vlan_interface
    oid_vrrp_status = '1.3.6.1.2.1.68.1.3.1.3'              # Append vrrp_id and provide vrrp_status_code
    oid_vrrp_id = '1.3.6.1.2.1.4.20.1.2'                    # Append vlan_interface and provide vrrp_id

    vlan_interfaces = plugin.queryNextSnmpOid(oid_vlan_interfaces)
    vrrp_status_table = plugin.queryNextSnmpOid(oid_vrrp_status)
    
    # Create the Vlan information tables
    #
    # Storing ID of Vlan and his associated IP address
    vlans = {}
    for vlan in vlan_interfaces:
        vlan_id = vlan[0][-1]
        vlans[vlan_id] = vlan[1].prettyPrint()
    
    # Store ID of VRRP and his associated status
    vrrps = {}
    for vrrp in vrrp_status_table:
        vrrp_id = vrrp[0][-2]
        vrid = vrrp[0][-1]
        vrrps[vrrp_id] = vrid

    # Format the long output
    longoutput = ""
    nbr_error = 0
    vrrp_calculation = 0
    for vlan_id in vlans:
        vrrp_id = plugin.querySnmpOid('%s.%s' % (oid_vrrp_id, vlans[vlan_id]))[1]
        # Show VLAN infos if vrrp_id is available
        if vrrp_id:
            vlan_name = plugin.querySnmpOid('%s.%s' % (oid_vlan_names, vlan_id))[1]
            try:
                vrrp_status_code = plugin.querySnmpOid('%s.%s.%s' % (oid_vrrp_status, vrrp_id, vrrps[vrrp_id]))[1]
            except KeyError:
                continue
        
            vrrp_calculation += vrrp_status_code
            longoutput += '%s: %s\n' % (vlan_name, plugin.vrrp_status[vrrp_status_code].title())

    # Format Nagios output
    longoutput = longoutput.rstrip('\n')
    if vrrp_calculation != plugin.params.warnthr:
        output = 'VRRP master has changed for at least one VLAN or VRRP VLAN configuration has changed !\n'
        plugin.warning(output + longoutput)
    else:
        output = 'VRRP status has not changed.\n'
        plugin.ok(output + longoutput)
