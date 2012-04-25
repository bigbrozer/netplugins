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
from shared import __version__
from monitoring.nagios.plugin.snmp import NagiosPluginSNMP

logger = log.getLogger('plugin')

# Plugin class
class IBMSanDirectorsCRC(NagiosPluginSNMP):
    def define_plugin_arguments(self):
        """Add extra specific arguments"""
        super(IBMSanDirectorsCRC, self).define_plugin_arguments()

        self.required_args.add_argument('-d',
                                        dest='delta',
                                        type=int,
                                        default=120,
                                        help="Make an average of <delta> seconds (default to 120 secs).",
                                        )
        self.required_args.add_argument('-w',
                                        dest='warning',
                                        type=int,
                                        help="Warn if average number of CRCs are above this threshold (see DELTA).",
                                        required=True,
                                        )
        self.required_args.add_argument('-c',
                                        dest='critical',
                                        type=int,
                                        help="Crit if average number of CRCs are above this threshold (see DELTA).",
                                        required=True,
                                        )

# The main procedure
progdesc = 'Check IBM SAN Directors for CRCs on ports.'

plugin = IBMSanDirectorsCRC(version=__version__, description=progdesc)
