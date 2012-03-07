#!/usr/bin/perl -w
#===============================================================================
# Name          : check_cisco_cpu_module.pl
# Author        : Thibaut COURVOISIER <thibaut.courvoisier-ext@faurecia.com>
# Description   : Check which CPU module is active on Cisco Core Switch.
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

use strict;
use Net::SNMP;
use Getopt::Long;
#use Data::Dumper::Simple;
use File::Basename;

# Program info
my $plugin_name = basename($0);

# SNMP info
my $session;
my $error;
my $oid_module_5 = '.1.3.6.1.4.1.9.9.176.1.1.2.0'; #Value of the primary CPU module
my $oid_module_6 = '.1.3.6.1.4.1.9.9.176.1.1.4.0'; #Value of secondary CPU module
my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);

my %CPU_STATES=(14=>'Active',9=>'StandByHot');

# Command line arguments
my $o_hostname = '';
my $o_community = '';
my $o_help = undef;

# *** CPU MODULE STATE : ***
#INTEGER {notKnown(1),
#disabled(2),
#initialization(3),
#negotiation(4),
#standbyCold(5),
#standbyColdConfig(6),
#standbyColdFileSys(7),
#standbyColdBulk(8),
#standbyHot(9),
#activeFast(10),
#activeDrain(11),
#activePreconfig(12),
#activePostconfig(13),
#active(14),
#activeExtraload(15),
#activeHandback(16)

# Linking arguments
GetOptions(
    'H=s' => \$o_hostname,
    'C=s' => \$o_community,
    'help' => \$o_help
);

# Checking arguments
if (defined($o_help)) { help(); exit 3; }
if (!defined($o_hostname) || !defined($o_community)) { help(); print "\nMissing hostname or SNMP community arguments. Check syntax.\n"; exit 3;  }

sub print_usage {
    print "Usage: $plugin_name -H <hostname/ip_address> -C <snmp_community> [-h]\n";
}

sub print_description {
    print <<EOT;
Description:
  Check which CPU module is active on Cisco Core Switch.

EOT
}

sub help {
   print "\n==== $plugin_name ====\n\n";
   print "Creative Commons Attribution-Noncommercial-Share Alike 2.0 France\n";
   print "(c)2010 Thibaut COURVOISIER, <thibaut.courvoisier-ext\@faurecia.com>\n\n";
   print_description();
   print_usage();
   print <<EOT;
 --help
   Print this help message.
 -H
   Hostname or IP address.
 -C
   SNMP Community.
EOT
}

sub get_cpu_status {
    my $resultat1 = $session->get_request($oid_module_5);
    my $resultat2 = $session->get_request($oid_module_6);

    if (!defined($resultat1 or $resultat2)) {
        printf("ERROR: Description table : %s.\n", $session->error);
        $session->close;
        exit $ERRORS{"UNKNOWN"};
    }
	
    if ($$resultat1{$oid_module_5} != 14) {
        printf("WARNING: primary CPU module aren't active !\n");
        $session->close;
        exit $ERRORS{"WARNING"};
    }
	
    #print "\n";
    #print Dumper($resultat1, $resultat2);

    my $nagios_output = "OK: Primary CPU module is active.\n";
    my $nagios_long_output = "";
    
    $nagios_long_output .= "CPU Module 5: ".$CPU_STATES{$$resultat1{$oid_module_5}}."\n";
    $nagios_long_output .= "CPU Module 6: ".$CPU_STATES{$$resultat2{$oid_module_6}}."\n";

    return $nagios_output.$nagios_long_output;
}

($session, $error) = Net::SNMP->session(
    -hostname  => $o_hostname,
    -version   => 2,
    -community => $o_community,
    -port      => 161,
    -timeout   => 10
);

if (!defined($session)) {
    printf("ERROR opening session: %s.\n", $error);
    exit 3;
}

print get_cpu_status();
