#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
#===============================================================================
# Name          : check_ibm_san_directors_crcs.py
# Authors       : Vincent BESANCON <besancon.vincent@gmail.com>
# Description   : Check IBM SAN Directors for CRCs on ports.
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

import logging as log
from pprint import pformat
import traceback
from time import time
from datetime import datetime
import math

from shared import __version__
from monitoring.nagios.plugin import NagiosPluginSNMP

logger = log.getLogger('plugin')

# Plugin init class
class IBMSanDirectorsCRC(NagiosPluginSNMP):

    def initialize(self):
        super(IBMSanDirectorsCRC, self).initialize()

        # Timestamp at execution
        self.runtime = time()
        logger.debug('-- Plugin runtime: %s' % self.runtime)

    def define_plugin_arguments(self):
        """Add extra specific arguments"""
        super(IBMSanDirectorsCRC, self).define_plugin_arguments()

        self.required_args.add_argument('-r',
                                        dest='avgrec',
                                        type=int,
                                        default=2,
                                        help="Make an average for the last <N> records (default to 2).",
                                        )
        self.required_args.add_argument('-w',
                                        dest='warning',
                                        type=int,
                                        help="Warn if average number of CRCs are above this threshold.",
                                        required=True,
                                        )
        self.required_args.add_argument('-c',
                                        dest='critical',
                                        type=int,
                                        help="Crit if average number of CRCs are above this threshold.",
                                        required=True,
                                        )

    def verify_plugin_arguments(self):
        super(IBMSanDirectorsCRC, self).verify_plugin_arguments()

        # Number of records
        if self.options.avgrec < 2: self.unknown('Number of records must be >= 2 to make an average !')

        # Thresholds
        if self.options.warning > self.options.critical:
            self.unknown('Warning threshold cannot be above critical !')
        elif self.options.warning < 0 or self.options.critical < 0:
            self.unknown('Warning / Critical threshold cannot be below zero !')


# Init plugin
progdesc = 'Check IBM SAN Directors for CRCs on ports.'

plugin = IBMSanDirectorsCRC(version=__version__, description=progdesc)

# Load any existing pickled data
try:
    # Load retention data
    retention_data = plugin.load_data()
except IOError:
    # No retention data to load
    retention_data = []

# Prepare SNMP query
oids = {
    'name': '1.3.6.1.4.1.1588.2.1.1.1.6.2.1.36',
    'alias': '1.3.6.1.4.1.1588.2.1.1.1.6.2.1.37',
    'crc': '1.3.6.1.4.1.1588.2.1.1.1.6.2.1.22',
}

query = plugin.snmp.getnext(oids)

# Dictionnary used to store gathered SNMP data and used by pickle for saving results
snmp_results = {
    'timestamp': plugin.runtime,
    'values': {},                   # Store SNMP results
}
try:
    for port in query['name']:
        data = snmp_results['values']
        name = port.pretty()
        alias = [a.pretty() for a in query['alias'] if a.index == port.index ][0]
        crc = [c.value for c in query['crc'] if c.index == port.index ][0]

        if alias:
            if not data.has_key(alias):
                data[alias] = {}

            if name:
                data[alias]['name'] = name
            else:
                data[alias]['name'] = 'No description'

            data[alias]['crc'] = crc
except KeyError:
    # That would mean unexpected result from the query (empty OID, etc...)
    message = """Unexpected error ! Please check plugin configuration.
If you see this message that would mean the query returned no result (empty OID) or the equipment does not
support such requests...

%s

Please check your plugin configuration first.""" % traceback.format_exc(limit=1)
    plugin.unknown(message)

logger.debug('-- SNMP data:')
logger.debug(pformat(snmp_results, indent=4))

# Save to pickle file the new data gathered
retention_data.append(snmp_results)
plugin.save_data(retention_data, limit=50)

# Calculate average time
last_records = retention_data[-plugin.options.avgrec:]
avg_record_time = 0
if len(retention_data) >= plugin.options.avgrec:
    calc_total_seconds = datetime.fromtimestamp(plugin.runtime) - datetime.fromtimestamp(last_records[0]['timestamp'])
    avg_record_time = int(math.ceil(calc_total_seconds.total_seconds()/60))
else:
    # Stop execution if not enough records in retention file. Wait next check.
    missing = plugin.options.avgrec - len(retention_data)
    plugin.unknown('Not enough data to generate average, need %d more checks. Waiting next check.' % missing)

# Calculate CRC increase
port_stats = {}

logger.debug('-- Processing pickled data for the last %d records.' % plugin.options.avgrec)
for data in last_records:
    index = last_records.index(data)
    val = data['values']
    prev_val = None

    if not index:
        continue
    else:
        prev_val = last_records[index-1]['values']
        logger.debug("Prev: %s, Next: %s" % (last_records[index-1]['timestamp'], data['timestamp']))

    for alias, stat in val.viewitems():
        name = stat['name']
        crc = stat['crc']
        prev_crc = prev_val[alias]['crc']

        if prev_val:
            prev_crc = prev_val[alias]['crc']

        if not port_stats.has_key(alias):
            port_stats[alias] = {'crc': 0}

        port_stats[alias]['name'] = name
        port_stats[alias]['crc'] += crc - prev_crc

logger.debug('port_stats:')
logger.debug(pformat(port_stats, indent=4))

# Define some Nagios related stuff used in output and status
nagios_output = ""
nagios_longoutput = ""
nagios_perfdata = " | "
nagios_status = None

errors = {
    'warning': [],
    'critical': [],
}

# Checking if we have port crc above or below thresholds
for port, stat in port_stats.viewitems():
    if plugin.options.warning < stat['crc'] <= plugin.options.critical:
        errors['warning'].append(port)
    elif stat['crc'] > plugin.options.critical:
        errors['critical'].append(port)

    nagios_perfdata += "\'Port_{name}\'={crc}c;{opt.warning};{opt.critical};0; ".format(crc=stat['crc'], name=port,
                                                                                     opt=plugin.options)

# Show short message in Nagios output
nbr_warn = len(errors['warning'])
nbr_crit = len(errors['critical'])
if not nbr_warn and not nbr_crit:
    nagios_status = plugin.ok
    nagios_output = "No CRC error detected on ports."
elif nbr_warn and not nbr_crit:
    nagios_status = plugin.warning
    nagios_output = "%d ports have warnings CRC errors !" % nbr_warn
elif nbr_crit and not nbr_warn:
    nagios_status = plugin.critical
    nagios_output = "%d ports have criticals CRC errors !" % nbr_crit
elif nbr_warn and nbr_crit:
    nagios_status = plugin.critical
    nagios_output = "%d ports have criticals, %d ports have warnings CRC errors !" % (nbr_crit, nbr_warn)

# Show average record time
nagios_output = "%s (Average on last %s mins)" % (nagios_output, avg_record_time)

# Check for errors details in long output
for status in errors:
    if len(errors[status]):
        nagios_longoutput += "\n{status} ({nbrerr}) (>= {thr}):\n".format(status=status.title(),
                                                                       nbrerr=len(errors[status]),
                                                                       thr=eval('plugin.options.{}'.format(status)))
        for alias in errors[status]:
            nagios_longoutput += "  Port %s: %d crc (%s)\n" % (
                alias,
                port_stats[alias]['crc'],
                port_stats[alias]['name'],
            )

# Output and return status to Nagios
output = nagios_output + nagios_longoutput + nagios_perfdata
nagios_status(output)
