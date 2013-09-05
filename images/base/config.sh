#!/bin/bash

set -e

HOST=`hostname`
echo "127.0.0.1 $HOST" >> /etc/hosts

for file in /docker/startup/*; do
  if test -f $file; then
    echo $file
    . $file
  fi
done

