#!/bin/bash

set -e
CGROUP=/sys/fs/cgroup/devices/lxc
[ -d $CGROUP ] || {
        echo "Please set CGROUP in $0 first."
        exit 1
}

BRIDGE=$1
[ "$BRIDGE" ] || {
        echo "$0 <bridge> [container=ip] [container=ip] [...]"
        exit 1
}

if [[ -z `brctl show | grep $BRIDGE` ]]; then
        echo "Creating bridge $BRIDGE."
        brctl addbr $BRIDGE
        ifconfig $BRIDGE up
fi

shift
while true
do
        SHORTID=$1
        IPADDR=$2
        LONGID=$(docker inspect $SHORTID | grep ID | cut -d\" -f4)
        [ "$LONGID" ] || {
                echo "WARNING: could not find container $SHORTID."
                continue
        }
        NSPID=$(head -n 1 $CGROUP/$LONGID/tasks)
        [ "$NSPID" ] || {
                echo "WARNING: could not find PID inside container $LONGID."
                continue
        }
        mkdir -p /var/run/netns
        rm -f /var/run/netns/$LONGID
        ln -s /proc/$NSPID/ns/net /var/run/netns/$LONGID
        R=$RANDOM
        IF_LOCAL_NAME=pvnetl$R
        IF_REMOTE_NAME=pvnetr$R
        ip link add name $IF_LOCAL_NAME type veth peer name $IF_REMOTE_NAME
        brctl addif $BRIDGE $IF_LOCAL_NAME
        ifconfig $IF_LOCAL_NAME up
        ip link set $IF_REMOTE_NAME netns $NSPID
        ip netns exec $LONGID ip link set $IF_REMOTE_NAME name eth1
        ip netns exec $LONGID ifconfig eth1 $IPADDR
        shift 2
        [ "$1" ] || break
done
