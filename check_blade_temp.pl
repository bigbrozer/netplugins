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
my $oid_temp_sensor_1 = '.1.3.6.1.4.1.1872.2.5.1.3.1.22.0'; #Value of the primary sensor
my $oid_temp_sensor_2 = '.1.3.6.1.4.1.1872.2.5.1.3.1.23.0'; #Value of secondary sensor
my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);


# Command line arguments
my $o_hostname = '';
my $o_community = '';
my $o_help = undef;


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
    print "Usage: $plugin_name -C <snmp_community> -H <hostname/ip_address>  ]\n";
}

sub print_description {
    print <<EOT;
Description:
  Check which temperature sensor are in good health.

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

sub temp_sensor {
	my $error="";
	my $nagios_output = "";
	my $nagios_long_output = "";
	my $cpt_error = 0;
    my $resultat1 = $session->get_request($oid_temp_sensor_1); #43.5 C (Warn at 90.0 C/Recover at 80.0 C)
    my $resultat2 = $session->get_request($oid_temp_sensor_2); #43.5 C (Warn at 90.0 C/Recover at 80.0 C)
	
	my @temp_elements = split(" ", $$resultat1{$oid_temp_sensor_1}); # s�paration de : 43.5 C (Warn at 90.0 C/Recover at 80.0 C)
	my $temp = $temp_elements[0]; # reccup�ration de : 43.5
	
	
	my @temp2_elements = split(" ", $$resultat2{$oid_temp_sensor_2}); # s�paration de : 43.5 C (Warn at 90.0 C/Recover at 80.0 C)
	my $temp2 = $temp2_elements[0]; # reccup�ration de : 43.5
	
	
    if (!defined($resultat1 or $resultat2)) {
        printf("ERROR: Description table : %s.\n", $session->error);
        $session->close;
        exit $ERRORS{"UNKNOWN"};
    }
	
    if ($temp > 55) {
		$cpt_error = $cpt_error + 1;
        $nagios_long_output = "WARNING: Primary temperature sensor is above the warning threshold !\n";
		$error = $ERRORS{"WARNING"};
		
	}
	
	if ($temp2 > 55) {
		$cpt_error = $cpt_error + 1;
		$nagios_long_output .= "WARNING: Secondary temperature sensor is above the warningthreshold !\n";
		$error = $ERRORS{"WARNING"};
    }
	
	
	if($temp > 70){
		$cpt_error = $cpt_error + 1;
        $nagios_long_output .= "CRITICAL: Primary temperature sensor is above the critical threshold !\n";
		$error = $ERRORS{"CRITICAL"};
		}
		
	if($temp2 > 70){
		$cpt_error = $cpt_error + 1;
        $nagios_long_output .= "CRITICAL: Secondary temperature sensor is above the critical threshold !\n";
		$error = $ERRORS{"CRITICAL"};
		}	
		
		
	if($cpt_error >= 1 ){
	$nagios_output = "Click to see that temperature sensor is above the threshold | 'Sensor_1'=".$temp."C;55;70; 'Sensor_2'=".$temp2."C;55;70;";
	$nagios_long_output .= "Primary sensor: ".$temp."\n";
    $nagios_long_output .= "Secondary sensor: ".$temp2."\n";
	$nagios_output .= "\n".$nagios_long_output;
	return $nagios_output;
	$session->close;
    exit $error;
	}
	
	else{
    $nagios_output = "OK: Temperature sensor are in good health. | 'Sensor_1'=".$temp."C;55;70; 'Sensor_2'=".$temp2."C;55;70;\n";    
    $nagios_long_output .= "Primary sensor: ".$temp."\n";
    $nagios_long_output .= "Secondary sensor: ".$temp2."\n";

    return $nagios_output.$nagios_long_output;
	}
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

print temp_sensor();
