#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
#===============================================================================
# Name          : check_cisco_cpu.py
# Author        : Vincent BESANCON <besancon.vincent@gmail.com>
# Description   : Check all CPUs usage on Cisco devices supporting CISCO-PROCESS-MIB.
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

# Specific class for this plugin
class CheckCiscoCPU(NagiosPluginSNMP):
    def define_plugin_arguments(self):
        """Define arguments for the plugin"""
        # Define common arguments
        super(CheckCiscoCPU, self).define_plugin_arguments()
        
        # Add extra arguments
        self.required_args.add_argument('-w', type=int, dest='warnthr', help='Warning threshold in percent (eg. 80)', required=True)
        self.required_args.add_argument('-c', type=int, dest='critthr', help='Critical threshold in percent (eg. 90)', required=True)


    def verify_plugin_arguments(self):
        """Do arguments checks"""
        super(CheckCiscoCPU, self).verify_plugin_arguments()

        # Be sure that warning is not above critical
        if self.options.warnthr > 100 or self.options.critthr > 100:
            raise self.unknown('Thresholds cannot be > 100 percent.')
        elif self.options.warnthr >= self.options.critthr:
            raise self.unknown('Warning threshold cannot be >= critical threshold.')


# The main procedure
progname = os.path.basename(sys.argv[0])
progdesc = 'Check all CPUs usage on Cisco devices supporting CISCO-PROCESS-MIB.'

plugin = CheckCiscoCPU(version=__version__, description=progdesc)

oids = {
    'entity_name': '1.3.6.1.2.1.47.1.1.1.1.7',
    'cpu_indexes': '1.3.6.1.4.1.9.9.109.1.1.1.1.2',
    'cpu_usages': '1.3.6.1.4.1.9.9.109.1.1.1.1.8',
}

logger.debug('====== Query host...')
query = plugin.snmp.getnext(oids)

cpu_data = {}
logger.debug('====== Getting name for CPU module...')
for i in range(0, len(query['cpu_usages'])):
    try:
        cpu_index = query['cpu_indexes'][i].value
        if cpu_index:
            logger.debug('\tCPU index found: %s' % cpu_index)
            cpu_name = [e.pretty() for e in query['entity_name'] if e.index == cpu_index][0]
        else:
            logger.debug('\tCPU index cannot be determined. Generating name...')
            raise KeyError()
    except KeyError:
        # Set a default name for the CPU module
        cpu_name = 'CPU%d' % i

    logger.debug('\tCPU name: %s' % cpu_name)
    cpu_data[cpu_name] = int(query['cpu_usages'][i].value)

# Checking values if in thresholds and formatting output
output = ""
longoutput = ""
exit_code = 0
nbr_error = 0
i = 1
for cpu in cpu_data:
    if plugin.options.warnthr < cpu_data[cpu] < plugin.options.critthr:
        longoutput += '* %s: %d%% * (>%d)\n' % (cpu, cpu_data[cpu], plugin.options.warnthr)
        if exit_code != 2: exit_code = 1
        nbr_error+=1
    elif cpu_data[cpu] > plugin.options.critthr:
        longoutput += '** %s: %d%% ** (>%d)\n' % (cpu, cpu_data[cpu], plugin.options.critthr)
        exit_code = 2
        nbr_error+=1
    elif cpu_data[cpu] < plugin.options.warnthr:
        longoutput += '%s: %d%% (<%d)\n' % (cpu, cpu_data[cpu], plugin.options.warnthr)

# Formatting perfdata
perfdata = " | "
for cpu in cpu_data:
    perfdata += '%s=%d%%;%d;%d;0;100 ' % (cpu.replace(' ', '_'), cpu_data[cpu], plugin.options.warnthr, plugin.options.critthr)

# Output to Nagios
longoutput = longoutput.rstrip('\n')

if not exit_code:
    output = 'All CPU usage are below thresholds.\n'
    longoutput += perfdata
    plugin.ok(output + longoutput)
elif exit_code == 1:
    output = '%d CPU are above %d%% of usage !\n' % (nbr_error, plugin.options.warnthr)
    longoutput += perfdata
    plugin.warning(output + longoutput)
elif exit_code == 2:
    output = '%d CPU are above %d%% of usage !\n' % (nbr_error, plugin.options.critthr)
    longoutput += perfdata
    plugin.critical(output + longoutput)

