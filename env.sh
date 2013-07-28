#!/bin/bash

PUBLIC_BRIDGE=br0
PUBLIC_IP_BASE=192.168.0.200

get_next_ip() {
	local ip=$1
	local offset=$2
	local baseaddr="$(echo $ip | cut -d. -f1-3)"
	local lsv="$(echo $ip | cut -d. -f4)"
	local new_number=$(( $lsv + $offset ))
	echo $baseaddr.$new_number
}

new_address=$(get_next_ip "192.168.0.200" 2)
echo $new_address

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi
