#! /bin/sh

## 2006-10-23, Ingo Lantschner (based on the work of Fredrik Wanglund)
## This Plugin returns the date configured on a cisco core switch

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

PROGNAME=`basename $0`
REVISION=`echo 'Revision: 0.2 ' `
NAGIOSPLUGSDIR=/usr/local/nagios/libexec

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
	echo "This plugin checks by SNMP the date which is configured on a Cisco core switch"
	echo "No Warning for this plugin"
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

CISCOCLOCK=$($NAGIOSPLUGSDIR/check_snmp -H $1 -C $2 -o  .1.3.6.1.4.1.9.9.168.1.1.10.0 | cut -d " " -f4,5,6,7,8,9,10,11 | tr -d [:space:]) 
CLOCKBIN=`echo "ibase=16;obase=2; $CISCOCLOCK" | bc | sed 's/\(.\{1,32\}\)..*/\1/'`
CLOCKDEC=`echo "ibase=2;obase=A; $CLOCKBIN" | bc`
CSTE="2208988800" 
CLOCKDECBIS=$(($CLOCKDEC-$CSTE))
CLOCKUNIX=`date -d @"$CLOCKDECBIS"`

echo $CLOCKUNIX
exit 3
esac