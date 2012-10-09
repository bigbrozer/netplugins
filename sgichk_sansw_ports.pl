#!/usr/bin/perl -w
# nagios: +epn
#
# This plugin is intended to check port status on SAN Switches
# using the FCMGMT-MIB (in the experimental branch)
#
############################## sgichk_sansw_ports.pl ##############
my $Version='1.0';
# Date : Apr 14, 2012
# Author  : Brent Bice
# Help : http://nagios.manubulon.com
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# Contrib : Patrick Proy, J. Jungmann, S. Probst, R. Leroy, M. Berger
# TODO : 
# Maybe put base directory for performance as an option
#################################################################
#
# Help : ./sgichk_sansw_ports.pl -h
#
use strict;
use Net::SNMP;
use Getopt::Long;

# Nagios specific

my $TIMEOUT = 15;
my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);

# SNMP Datas

my $name_table= '.1.3.6.1.3.94.1.10.1.17';
my $physport_table = '.1.3.6.1.3.94.1.10.1.18';
my $state_table = '.1.3.6.1.3.94.1.10.1.6';
my $status_table = '.1.3.6.1.3.94.1.10.1.7';
my $hwstate_table = '.1.3.6.1.3.94.1.10.1.23';

my $admin_ok_val = 2;   # The value if a port is administratively up
my $port_ok_val = 3;    # The value if a port is operationally up

my %pstatus=(
   1=>'UNKNOWN',
   2=>'UNUSED',
   3=>'READY',
   4=>'WARNING',
   5=>'FAILURE',
   6=>'Not-Participating',
   7=>'INITIALIZING',
   8=>'BYPASS',
   9=>'OLS'
);

my %pstate=(
   1=>'UNKNOWN',
   2=>'ONLINE',
   3=>'OFFLINE',
   4=>'BYPASSED',
   5=>'DIAGNOSTICS'
);

my %hwstate=(
   1=>'UNKNOWN',
   2=>'FAILED',
   3=>'BYPASSED',
   4=>'ACTIVE',
   5=>'LOOPBACK',
   6=>'TXFAULT',
   7=>'NOMEDIA',
   8=>'LINKDOWN'
);

# QLogic specific stuff
my $QLstate_table = '.1.3.6.1.4.1.1663.1.3.10.1.1.3';
my $QLstatus_table = '.1.3.6.1.4.1.1663.1.3.10.1.1.4';

my %QLpstatus=(
   1=>'ONLINE',
   2=>'OFFLINE',
   3=>'TESTING',
   4=>'FAILURE'
);

my %QLpstate=(
   1=>'ONLINE',
   2=>'OFFLINE',
   3=>'TESTING',
   4=>'FAILURE'
);

# Globals


# Standard options
my $o_host = 		undef; 	# hostname
my $o_port = 		161; 	# port
my $o_descr =		'.*'; 	# description filter
my $o_help=		undef; 	# wan't some help ?
my $o_verb=		undef;	# verbose mode
my $o_version=		undef;	# print version

my $o_timeout=  undef; 		# Timeout (Default 5)
# SNMP Message size parameter (Makina Corpus contrib)
my $o_octetlength=undef;
# Login options specific
my $o_community = 	undef; 	# community
my $o_version1	= undef;	#use snmp v1
my $o_version2	= undef;	#use snmp v2c
my $o_login=	undef;		# Login for snmpv3
my $o_passwd=	undef;		# Pass for snmpv3
my $v3protocols=undef;	# V3 protocol list.
my $o_authproto='md5';		# Auth protocol
my $o_privproto='des';		# Priv protocol
my $o_privpass= undef;		# priv password

my $o_qlogic=		undef;	# QLogic mode

# functions

sub p_version { print "check_snmp_int version : $Version\n"; }

sub print_usage {
    print "Usage: $0 [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>)  [-p <port>] [-o <octet_length>] [-t <timeout>] [-V] --qlogic\n";
}

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub help {
   print "\nSAN Switch Interface Check for Nagios version ",$Version,"\n";
   print_usage();
   print <<EOT;
-v, --verbose
   print extra debugging information (including interface list on the system)
-h, --help
   print this help message
-H, --hostname=HOST
   name or IP address of host to check
-C, --community=COMMUNITY NAME
   community name for the host's SNMP agent (implies v1 protocol)
-l, --login=LOGIN ; -x, --passwd=PASSWD, -2, --v2c
   Login and auth password for snmpv3 authentication 
   If no priv password exists, implies AuthNoPriv 
   -2 : use snmp v2c
-X, --privpass=PASSWD
   Priv password for snmpv3 (AuthPriv protocol)
-L, --protocols=<authproto>,<privproto>
   <authproto> : Authentication protocol (md5|sha : default md5)
   <privproto> : Priv protocole (des|aes : default des) 
-P, --port=PORT
   SNMP port (Default 161)
-o, --octetlength=INTEGER
  max-size of the SNMP message, usefull in case of Too Long responses.
  Be carefull with network filters. Range 484 - 65535, default are
  usually 1472,1452,1460 or 1440.     
-t, --timeout=INTEGER
   timeout for SNMP in seconds (Default: 5)   
-V, --version
   prints version number
--qlogic
   Use this switch if you're monitoring a Qlogic switch. They don't fully
   support the MIBs this plugin uses.
EOT
}

# For verbose output
sub verb { my $t=shift; print $t,"\n" if defined($o_verb) ; }

sub check_options {
    Getopt::Long::Configure ("bundling");
	GetOptions(
   	'v'	=> \$o_verb,		'verbose'	=> \$o_verb,
        'h'     => \$o_help,    	'help'        	=> \$o_help,
        'H:s'   => \$o_host,		'hostname:s'	=> \$o_host,
        'p:i'   => \$o_port,   		'port:i'	=> \$o_port,
        'C:s'   => \$o_community,	'community:s'	=> \$o_community,
	'1'	=> \$o_version1,	'v1'		=> \$o_version1,
	'2'	=> \$o_version2,	'v2c'		=> \$o_version2,

	'l:s'	=> \$o_login,		'login:s'	=> \$o_login,
	'x:s'	=> \$o_passwd,		'passwd:s'	=> \$o_passwd,
	'X:s'	=> \$o_privpass,		'privpass:s'	=> \$o_privpass,
	'L:s'	=> \$v3protocols,		'protocols:s'	=> \$v3protocols,   
        't:i'   => \$o_timeout,    	'timeout:i'	=> \$o_timeout,
	'o:i'   => \$o_octetlength,    	'octetlength:i' => \$o_octetlength,

	'qlogic'		=> \$o_qlogic
    );
    if (defined ($o_help) ) { help(); exit $ERRORS{"UNKNOWN"}};
    if (defined($o_version)) { p_version(); exit $ERRORS{"UNKNOWN"}};
    if ( ! defined($o_host) ) # check host
	{ print_usage(); exit $ERRORS{"UNKNOWN"}}

    # check snmp information
    if ( !defined($o_community) && (!defined($o_login) || !defined($o_passwd)) )
	{ print "Put snmp login info!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
    if ((defined($o_login) || defined($o_passwd)) && (defined($o_community) || defined($o_version2)) )
	{ print "Can't mix snmp v1,2c,3 protocols!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
    if (defined ($v3protocols)) {
	  if (!defined($o_login)) { print "Put snmp V3 login info with protocols!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	  my @v3proto=split(/,/,$v3protocols);
	  if ((defined ($v3proto[0])) && ($v3proto[0] ne "")) {$o_authproto=$v3proto[0];	}	# Auth protocol
	  if (defined ($v3proto[1])) {$o_privproto=$v3proto[1];	}	# Priv  protocol
	  if ((defined ($v3proto[1])) && (!defined($o_privpass))) {
	    print "Put snmp V3 priv login info with priv protocols!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
    }
    if (defined($o_timeout) && (isnnum($o_timeout) || ($o_timeout < 2) || ($o_timeout > 60))) 
	  { print "Timeout must be >1 and <60 !\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
    if (!defined($o_timeout)) {$o_timeout=5;}

    #### octet length checks
    if (defined ($o_octetlength) && (isnnum($o_octetlength) || $o_octetlength > 65535 || $o_octetlength < 484 )) {
		print "octet lenght must be < 65535 and > 484\n";print_usage(); exit $ERRORS{"UNKNOWN"};
    }	

   # QLogic switches don't support this experimental MIB completely
   if ($o_qlogic) {
      $admin_ok_val = 1;   # The value if a port is administratively up
      $port_ok_val = 1;    # The value if a port is operationally up
   }
}
    
########## MAIN #######

check_options();

verb ("admin_ok_val = $admin_ok_val");
verb ("port_ok_val = $port_ok_val");

# Check gobal timeout if snmp screws up
if (defined($TIMEOUT)) {
  verb("Alarm at $TIMEOUT + 5");
  alarm($TIMEOUT+5);
} else {
  verb("no timeout defined : $o_timeout + 10");
  alarm ($o_timeout+10);
}

$SIG{'ALRM'} = sub {
 print "No answer from host\n";
 exit $ERRORS{"UNKNOWN"};
};

# Connect to host
my ($session,$error);
if ( defined($o_login) && defined($o_passwd)) {
  # SNMPv3 login
  if (!defined ($o_privpass)) {
  verb("SNMPv3 AuthNoPriv login : $o_login, $o_authproto");
    ($session, $error) = Net::SNMP->session(
      -hostname   	=> $o_host,
      -version		=> '3',
      -port      	=> $o_port,
      -username		=> $o_login,
      -authpassword	=> $o_passwd,
      -authprotocol	=> $o_authproto,
      -timeout          => $o_timeout
    );  
  } else {
    verb("SNMPv3 AuthPriv login : $o_login, $o_authproto, $o_privproto");
    ($session, $error) = Net::SNMP->session(
      -hostname   	=> $o_host,
      -version		=> '3',
      -username		=> $o_login,
      -port      	=> $o_port,
      -authpassword	=> $o_passwd,
      -authprotocol	=> $o_authproto,
      -privpassword	=> $o_privpass,
	  -privprotocol => $o_privproto,
      -timeout          => $o_timeout
    );
  }
} else {
  if (defined ($o_version2)) {
    # SNMPv2c Login
	verb("SNMP v2c login");
	($session, $error) = Net::SNMP->session(
       -hostname  => $o_host,
	   -version   => 2,
       -community => $o_community,
       -port      => $o_port,
       -timeout   => $o_timeout
    );
  } else {
    # SNMPV1 login
	verb("SNMP v1 login");
    ($session, $error) = Net::SNMP->session(
       -hostname  => $o_host,
       -community => $o_community,
       -port      => $o_port,
       -timeout   => $o_timeout
    );
  }
}
if (!defined($session)) {
   printf("ERROR opening session: %s.\n", $error);
   exit $ERRORS{"UNKNOWN"};
}

if (defined($o_octetlength)) {
	my $oct_resultat=undef;
	my $oct_test= $session->max_msg_size();
	verb(" actual max octets:: $oct_test");
	$oct_resultat = $session->max_msg_size($o_octetlength);
	if (!defined($oct_resultat)) {
		 printf("ERROR: Session settings : %s.\n", $session->error);
		 $session->close;
		 exit $ERRORS{"UNKNOWN"};
	}
	$oct_test= $session->max_msg_size();
	verb(" new max octets:: $oct_test");
}

# Get port state table
my $resultstate = $session->get_table( Baseoid => $state_table );
if (!defined($resultstate)) {
   printf("ERROR: Port State table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}

# Get port status table
my $resultstatus = $session->get_table( Baseoid => $status_table );
if (!defined($resultstatus)) {
   printf("ERROR: Port Status table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}

# Get port name table
my $resultname = $session->get_table( Baseoid => $name_table );
if (!defined($resultname)) {
   verb("ERROR: Port Name table : " . $session->error . ".\n");
}

# Get physport table
my $resultphysport = $session->get_table( Baseoid => $physport_table );
if (!defined($resultphysport)) {
   verb("ERROR: Physical Port table : " . $session->error . ".\n");
}

# Get hwstate table
my $resulthwstate = $session->get_table( Baseoid => $hwstate_table );
if (!defined($resulthwstate)) {
   verb("ERROR: Port HWState table : " . $session->error . ".\n");
}

# If we're running a dumb old QLogic switch...
my $resultQLstate = undef;
my $resultQLstatus = undef;
if (defined($o_qlogic)) {
   # Get port state table
   $resultQLstate = $session->get_table( Baseoid => $QLstate_table );
   if (!defined($resultQLstate)) {
      printf("ERROR: QLogic Port State table : %s.\n", $session->error);
      $session->close;
      exit $ERRORS{"UNKNOWN"};
   }
   
   # Get port status table
   $resultQLstatus = $session->get_table( Baseoid => $QLstatus_table );
   if (!defined($resultQLstatus)) {
      printf("ERROR: QLogic Port Status table : %s.\n", $session->error);
      $session->close;
      exit $ERRORS{"UNKNOWN"};
   }
}

$session->close;

# Only a few seconds left...
alarm(5);

my $num_int = 0;
my $num_ok=0;
my @msgs=();

my $print_out = "";

foreach my $key ( keys %$resultstate) {
   #verb("OID : $key, State : $$resultstate{$key}");

   # Get the port index
   my $pindex = "";
   if ($key =~ /^$state_table\.(.*)/) { $pindex = $1; }

   my @oid_list = split (/\./,$pindex); 
   my $ifnum = pop(@oid_list);
   my $QLpindex = ".1.$ifnum";

   # Get the admin status of the port
   my $adminstat = undef;
   if (defined($o_qlogic)) {
      $adminstat = $$resultQLstate{$QLstate_table . $QLpindex};
   } else {
      $adminstat = $$resultstate{$key};
   }

   if ($adminstat == $admin_ok_val) {   # port is ONLINE...
      $num_int++;   # We have an administratively up port

      # Get the port status
      my $status = undef;
      if (defined($o_qlogic)) {
         $status = $$resultQLstatus{$QLstatus_table . $QLpindex};
      } else {
         $status = $$resultstatus{$status_table . "." . $pindex};
      }

      # If we were able to fetch the next few tables, get their values
      # for this port too
      my $physport = "unknown";
      my $pname = undef;
      my $phwstate = 1;   # Port HWState = UNKNOWN
      if (defined($resultphysport)) {
         $physport = $$resultphysport{$physport_table . "." . $pindex};
      }
      if (defined($resultname)) {
         $pname = $$resultname{$name_table . "." . $pindex};
      }
      if (defined($resulthwstate)) {
         $phwstate = $$resulthwstate{$hwstate_table . "." . $pindex};
      }

      my $msg = "";
      if (defined($pname)) {
         $msg = "Port $physport: Name=$pname";
      } else {
         $msg = "Port $physport";
      }

      if (defined($o_qlogic)) {
         $msg .= " - Status=$QLpstatus{$status}";
      } else {
         $msg .= " - Status=$pstatus{$status}";
      }
      $msg .= " HWState=$hwstate{$phwstate}";
      verb($msg);

      if ($status == $port_ok_val) {   # if port status is "READY"...
         $num_ok++;
	 push (@msgs, $msg);
      } else {
         push (@msgs, $msg);
      }
   }
}

# If the number of administratively up ports is the same as the number of
# "OK" ports...
if ($num_int == $num_ok) {
   print "OK: All $num_ok ports are up \n";
   foreach (sort @msgs) {
      print "$_\n";
   }

   exit $ERRORS{"OK"};
} else {
   print "CRITICAL: $num_ok out of $num_int ports are up\n";
   foreach (sort @msgs) {
      print "$_\n";
   }
   exit $ERRORS{"CRITICAL"};
}

