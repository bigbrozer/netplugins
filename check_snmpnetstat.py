#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
#===============================================================================
# Filename      : check_snmpnetstat.py
# Author        : Vincent BESANCON <besancon.vincent@gmail.com>
# Description   : check the number of tcp or udp connection using command
#                 'snmpnetstat' (filters available).
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

import os, sys, argparse, subprocess, re

from shared import __version__

#-------------------------------------------------------------------------------
## START OF CONFIGURATION ######################################################

# Commands location
snmpnetstat='/usr/bin/env snmpnetstat'

# Default snmpnetstat command argument
snmpnetstat_opts = "-c {0.community} -v{0.version} {0.no_dns} -Cp {0.protocol} {0.hostname}"

######################################################## END OF CONFIGURATION ##
#-------------------------------------------------------------------------------

###################
####  Globals  ####
###################

# Nagios
nagios_state = "OK"
nagios_output = ""
nagios_thresholds = ""
nagios_exit_code = 0

#############################
####  Arguments parsing  ####
#############################

progname = os.path.basename(sys.argv[0])

parser = argparse.ArgumentParser(description='Check the number of tcp or udp connection using \'snmpnetstat\'.',
                                 usage='%(prog)s -H <hostname> [-C <community] [-2] [-d | --debug] [-p <protocol>] [-m | --match PATTERN] [-w <warn_threshold> -c <crit_threshold>]')

parser_required_group = parser.add_argument_group('Required arguments')
parser_required_group.add_argument("-H", dest="hostname", help="The hostname to probe", required=True)

parser_extra_group = parser.add_argument_group('Extra arguments')
parser_extra_group.add_argument("-C", dest="community", default='public',
                    help="The SNMP community to use (default 'public' if not set)")
parser_extra_group.add_argument("-2", action="store_true", dest="version", help="Use SNMP version 2c (default 'v1' if not set)")
parser_extra_group.add_argument("-w", dest="warning", default=0, type=int, help="Warning threshold (none if not set)")
parser_extra_group.add_argument("-c", dest="critical", default=0, type=int, help="Critical threshold (none if not set)")
parser_extra_group.add_argument("-p", dest="protocol", choices=['tcp', 'udp'], default='tcp',
                    help="Protocol to check for (default 'tcp')")
parser_extra_group.add_argument("-d", "--debug", action="store_true", dest="debug",
                    help="Show debug information, Nagios may truncate output")
parser_extra_group.add_argument("-m", "--match", dest="match", default='',
                    help="Show only lines that match this string (default to 'all')")
parser_extra_group.add_argument("--no-dns", action="store_true", dest="no_dns",
                    help="Do not try to use DNS to interpret IP addresses (off by default)")
parser.add_argument('--version', action='version', version='%s %s' % (progname, __version__))

# Parse arguments on command line
options = parser.parse_args()

#########################
####  Sanity checks  ####
#########################

# Show debug message if debug is on
def debug(message):
    if options.debug:
        sys.stderr.write(message)

# Check the thresholds range
if options.warning > 0 or options.critical > 0:
    if options.warning > options.critical:
        sys.stderr.write("Warning could not be greater than critical !\n")
        sys.exit(3)

# Set default match pattern (depending on which protocol to check for)
if not len(options.match):
    options.match = r'^%s' % options.protocol

# Set SNMP version to use (v1 by default)
if options.version:
    options.version = '2c'
else:
    options.version = '1'

# Should we disable usage of DNS ?
if options.no_dns:
    options.no_dns = '-Cn'
else:
    options.no_dns = ''

###############################
####  Commands processing  ####
###############################

# Prepare command argument with the ones provided by user
snmpnetstat_opts = snmpnetstat_opts.format(options)
command = '%s %s' % (snmpnetstat, snmpnetstat_opts)

debug("Debug is on.\n")
debug("Command being executed: %s\n" % command)
proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out = proc.stdout.readlines()
err = proc.stderr.read()

# Check if there was any error
if len(err) > 0:
    sys.stderr.write(err)
    sys.exit(3)
elif not len(out) > 0:
    sys.stderr.write('UNKNOWN - No output from snmpnetstat !')
    sys.exit(3)

# Start counting the number of connection found
nbrConn = 0
debug("Using pattern: %s\n" % options.match)
debug("Getting output... (please wait):\n")
for line in out:
    if re.search(options.match, line):
        debug(line)
        nbrConn+=1

# Check if number of connection found is in thresholds range
if options.warning > 0 or options.critical > 0:
    nagios_thresholds = "(<%s)" % options.warning

    if options.warning < nbrConn < options.critical:
        nagios_state = "WARNING"
        nagios_thresholds = "(>%s) (<%s)" % (options.warning, options.critical)
        nagios_exit_code = 1
    if nbrConn > options.critical:
        nagios_state = "CRITICAL"
        nagios_thresholds = "(>%s)" % options.critical
        nagios_exit_code = 2

# Prepare Nagios output
nagios_output = "%s - %d connection(s) using pattern '%s' %s | 'nbrConn'=%d;;;;\n" % (nagios_state, nbrConn,
                                                                                      options.match, nagios_thresholds,
                                                                                      nbrConn)

sys.stdout.write(nagios_output)
sys.exit(nagios_exit_code)
