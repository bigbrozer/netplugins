#! /bin/sh

## 2006-10-23, Ingo Lantschner (based on the work of Fredrik Wanglund)
## This Plugin return the uptime for a cisco swith/router

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

PROGNAME=`basename $0`
REVISION=`echo 'Revision: 0.2 ' `
NAGIOSPLUGSDIR=/usr/local/nagios/libexec
WARN=$3
CRIT=$4

print_usage() {
	echo "Usage: $PROGNAME <host> <community> <warning> <critical>"
}

print_revision() {
	echo $PROGNAME  - $REVISION
}
print_help() {
	print_revision 
	echo ""
	print_usage
	echo ""
	echo "This plugin checks the Uptime through SNMP"
	echo "The treshholds (warning, critical) are in days"
	echo ""
	exit 0
}

case "$1" in
	--help)
		print_help
		exit 0
		;;
	-h)
		print_help
		exit 0
		;;
	--version)
	   	print_revision $PROGNAME $REVISION
		exit 0
		;;
	-V)
		print_revision $PROGNAME $REVISION
		exit 0
		;;
	*)

## Einige Plausibilitaetstest

if [ $# -lt 4 ]; then
   print_usage
   exit 3
   fi

if [ $WARN -lt $CRIT ]; then
   echo warning-level must be above the critical!
   exit 3
   fi


## Now we start checking ...

UPT=$($NAGIOSPLUGSDIR/check_snmp -H $1 -C $2 -o  .1.3.6.1.6.3.10.2.1.3.0 -w $3 -c $4 | cut -d " " -f 4) 
RES=$?

UPTMIN=$(expr $(echo $UPT | cut -d "*" -f2) / 60 )

if  [ $RES = 0 ]; then
   UPTDAY=$(expr $UPTMIN / 60 / 24 )
      if [ $UPTDAY -lt $CRIT ]; then  
         echo CRITICAL: Systemuptime $UPTMIN min.
         exit 2
         fi

      if [ $UPTDAY -lt $WARN ]; then  
         echo WARNING: Systemuptime $UPTMIN min.
         exit 1
         fi

      if [ $UPTDAY -ge $WARN ]; then  
         echo OK: Systemuptime $UPTDAY days
         exit 0
         fi

   fi

echo $UPT
exit 3

esac
