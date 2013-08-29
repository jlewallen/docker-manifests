#!/bin/bash

IFACE=eth1
while ! ifconfig $IFACE; do
  echo "Pausing"
  sleep 1
done
