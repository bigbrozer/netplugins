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

# Create OptionParser instance
argparser = optparse.OptionParser()

# Defining plugin arguments
argparser.add_option("-H", dest="hostname", help="OFTP server address")
argparser.add_option("-p", dest="port", help="OFTP server port", type="int")
argparser.add_option("-t", dest="timeout", help="Response timeout (default: 5 secs)", type="float", default="5.0")

# Tell OptionParser to parse all args and return their values
arguments = argparser.parse_args()[0]

# Check presence of mandatory arguments
if not arguments.hostname or not arguments.port:
    print "UNKNOWN - Syntax error, missing connection information !"
    raise SystemExit(3)

# Establish a connection and catch any possible error
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((arguments.hostname, arguments.port))
except socket.error:
    print "CRITICAL - Cannot establish a connection to OFTP server !"
    raise SystemExit(2)

# Set socket timeout, answer should be given in this amount af seconds
s.settimeout(arguments.timeout)

# Get data from the server and process response
try:
    while 1:
        data = s.recv(32)
        result = data.decode('utf-8')
        if "READY" in result:
            nagios_output = "OK - OFTP server is available."
            raise SystemExit(0)
except socket.timeout:
    nagios_output = "CRITICAL - OFTP server is reachable but did not answered in time !"
    raise SystemExit(2)
finally:
    s.close()
    print nagios_output
