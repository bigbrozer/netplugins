# -*- coding: UTF-8 -*-
#===============================================================================
# Filename      : fabfile.py
# Author        : Vincent BESANCON <besancon.vincent@gmail.com>
# Description   : fabric tasks
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

from fabric.api import task, cd, roles, put, run
from monitoring.fabric import servers

@task
@roles('central')
def upload():
    """Upload Debian package to central APT repository."""
    run('rm -f /var/www/packages/apt/plugin-network_*.deb')
    run('rm -f /var/www/packages/apt/plugin-check-snmpnetstat_*.deb')
    put('pkg-build/*.deb', '/var/www/packages/apt')
    with cd('/var/www/packages/apt'):
        run('dpkg-scanpackages -m . > Packages')

@task
@hosts('localhost')
def build():
    """Build the package."""
    local("git-buildpackage")

@task
@hosts('localhost')
def tag():
    """Tag package version."""
    local("git-buildpackage --git-tag-only")
