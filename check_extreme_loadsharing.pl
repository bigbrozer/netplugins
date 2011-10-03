#!/usr/bin/perl -w
#===============================================================================
# Name          : check_cisco_cpu_module.pl
# Author        : Thibaut COURVOISIER <thibaut.courvoisier-ext@faurecia.com>
# License       : Creative Commons Attribution-Noncommercial-Share Alike 2.0 France
# Description   : Check which CPU module is active on Cisco Core Switch.
#-------------------------------------------------------------------------------
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

my $loadsharing_table = '.1.3.6.1.4.1.1916.1.4.3.1.4'; 
my $loadsharing_oid ="";
my $loadsharing = "";

my $descr_table = '1.3.6.1.2.1.2.2.1.2';
my $descr_oid ="";
my $name ="";

my $nagios_output ="";
my $nagios_long_output = "";
my $cpt_error =0;



my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);

my %loadsharing_STATES=(1=>'Active',2=>'not In Service',3=>'not Ready', 4=>'create and Go', 5=>'create and Wait', 6=>'Destroy');
#active(1),
#notInService(2),
#notReady(3),
#createAndGo(4),
#createAndWait(5),
#destroy(6)


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
    print "Usage: $plugin_name -H <hostname/ip_address> -C <snmp_community> [-h]\n";
}

sub print_description {
    print <<EOT;
Description:
  check the load Sharing on extreme core switch.

EOT
}

sub help {
   print "\n==== $plugin_name ====\n\n";
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

sub get_load_sharing {

	my $oid_table = $session->get_table(
	Baseoid => $loadsharing_table );

foreach my $oid (keys (%$oid_table))  # Recupére les clés du hash contenu dans la variable $oid_table et les stock dans $oid.
{
	
	# ** Alias **
	my @oid_elements = split(/\./, $oid); # découpage en element nos clés
	my $alias = $oid_elements[-2].".".$oid_elements[-1];        # recuppération de l'alias en prennant que les deux derniers element des clés, particularité du loadsharing.
	
	$loadsharing_oid = $loadsharing_table.".".$alias;
	$loadsharing = $session->get_request($loadsharing_oid);	
	
	$descr_oid = $descr_table.".".$oid_elements[-1];
	$name = $session->get_request($descr_oid);	
	
    if (!defined($loadsharing)) {
        printf("ERROR: Description table : %s.\n", $session->error);
        $session->close;
        exit $ERRORS{"UNKNOWN"};
    }
	
    if ($$loadsharing{$loadsharing_oid} != 1) {
	    $nagios_long_output .= $$name{$descr_oid}." is: ".$loadsharing_STATES{$$loadsharing{$loadsharing_oid}}."\n";
        $cpt_error = $cpt_error +1;
    }
	
	$nagios_long_output .= $$name{$descr_oid}." is: ".$loadsharing_STATES{$$loadsharing{$loadsharing_oid}}."\n";
	
}	
	if ($cpt_error > 0)
{	
	$nagios_output = "WARNING: Load Sharing have a problem!\n";
	$nagios_output = $nagios_output."\n".$nagios_long_output;
	return $nagios_output;
    $session->close;
	exit $ERRORS{"WARNING"};
}	
    $nagios_output = "OK: Load Sharing is active.";  
	return $nagios_output = $nagios_output."\n".$nagios_long_output;

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

print get_load_sharing();

