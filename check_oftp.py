#!/usr/bin/env python2.7
#===============================================================================
# -*- coding: UTF-8 -*-
# Module        : check_oftp
# Author        : Vincent BESANCON aka 'v!nZ' <besancon.vincent@gmail.com>
#                                             <vincent.besancon@faurecia.com>
# Description   : Plugin to check if a OFTP server is available.
#-------------------------------------------------------------------------------
# This file is part of check_oftp.
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with check_oftp.  If not, see <http://www.gnu.org/licenses/>.
#===============================================================================

import socket
import optparse
import logging
import time


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger('plugin')

# Create OptionParser instance
argparser = optparse.OptionParser()

# Defining plugin arguments
argparser.add_option("-H", dest="hostname", help="OFTP server address")
argparser.add_option("-p", dest="port", help="OFTP server port", type=int)
argparser.add_option("-t", dest="timeout", help="Response timeout (default: 30 secs)", type=float, default="30")
argparser.add_option("--debug", dest="debug", help="Enable debugging", action='store_true')

# Tell OptionParser to parse all args and return their values
arguments = argparser.parse_args()[0]

# Check presence of mandatory arguments
if not arguments.hostname or not arguments.port:
    print "UNKNOWN - Syntax error, missing connection information !"
    raise SystemExit(3)

# Enable debug messages ?
if arguments.debug:
    logger.setLevel(logging.DEBUG)

# Establish a connection and catch any possible error
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(arguments.timeout)
    s.connect((arguments.hostname, arguments.port))
    s.setblocking(0)

    logger.debug('Successfully connected to socket.')
except socket.error:
    print "CRITICAL - Cannot establish a connection to OFTP server !"
    raise SystemExit(2)

# Get data from the server and process response
nagios_output = ""
try:
    start_time = time.time()

    while 1:
        # Break if timeout is reached
        remaining_time = time.time()-start_time
        if remaining_time > arguments.timeout:
            logger.error('Timeout reached')
            nagios_output = "CRITICAL - OFTP server is reachable but no data was received !"
            raise SystemExit(2)

        # Get some data from socket
        try:
            data = s.recv(32)
            result = data.decode('utf-8')
            if "READY" in result:
                nagios_output = "OK - OFTP server is available."
                raise SystemExit(0)
        except socket.error:
            # No data yet, make CPU happy ;-)
            time.sleep(0.1)
except socket.timeout:
    nagios_output = "CRITICAL - Unable to connect to OFTP server within %d seconds !" % arguments.timeout
    raise SystemExit(2)
finally:
    s.close()
    print nagios_output
