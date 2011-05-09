#! /bin/sh

## 2006-10-23, Ingo Lantschner (based on the work of Fredrik Wanglund)
## This Plugin returns if the blade switch has rebooted

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

PROGNAME=`basename $0`
REVISION=`echo 'Revision: 0.2 ' `
NAGIOSPLUGSDIR=/usr/local/nagios/libexec
WARN=$3
CRIT=$4

print_usage() {
	echo "Usage: $PROGNAME <host> <community>"
}

print_revision() {
	echo $PROGNAME  - $REVISION
}
print_help() {
	print_revision 
	echo ""
	print_usage
	echo ""
	echo "This plugin checks by SNMP the blade last boot and compares it with the date"
	echo "If date and last boot are equals, there is an alert for 2 days."
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

if [ $# -lt 2 ]; then
   print_usage
   exit 3
   fi

## Now we start checking ...
export DATE=`date`
DATEY=`echo $DATE | cut -d ":" -f3 | cut -d " " -f3`
DATEM=`echo $DATE | cut -d " " -f2`
DATED=`echo $DATE | cut -d " " -f3`


CISCOY=$($NAGIOSPLUGSDIR/check_snmp -H $1 -C $2 -o  .1.3.6.1.4.1.1872.2.5.1.3.1.12.0 | cut -d " " -f8) 
CISCOM=$($NAGIOSPLUGSDIR/check_snmp -H $1 -C $2 -o  .1.3.6.1.4.1.1872.2.5.1.3.1.12.0 | cut -d " " -f6) 
CISCOD=$($NAGIOSPLUGSDIR/check_snmp -H $1 -C $2 -o  .1.3.6.1.4.1.1872.2.5.1.3.1.12.0 | cut -d "," -f1 | cut -d " " -f7) 


echo $DATEY $DATEM $DATED
echo $CISCOY $CISCOM $CISCOD


if [[ "$DATEY" -eq "$CISCOY" && "$DATEM" -eq "$CISCOM" && "$DATED" -eq "$CISCOD" ]]; then 
         echo WARNING: The blade has rebooted.
         exit 1
         fi


		 
if [[ "$DATEY" -eq "$CISCOY" && "$DATEM" -eq "$CISCOM" && "$DATED" -eq "`expr $CISCOD + 1`" ]]; then
         echo WARNING: The blade did reboot one day ago.
         exit 1
         fi
		 
echo "No problem, the blade hasn't rebooted recently"
exit 0

esac
