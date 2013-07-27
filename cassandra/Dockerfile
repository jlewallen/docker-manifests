from jlewallen/base

maintainer Jacob Lewallen

run mkdir -p /opt
run cd /opt && wget http://apache.mirrors.hoobly.com/cassandra/1.2.7/apache-cassandra-1.2.7-bin.tar.gz 
run cd /opt && tar zxf apache-cassandra-*.tar.gz
run rm /opt/*.tar.gz
run mv /opt/apache-cassandra-* /opt/cassandra
add cassandra-env.sh /opt/cassandra/conf/cassandra-env.sh
add start /opt/cassandra/bin/start
run chmod 755 /opt/cassandra/bin/start

expose 7000
expose 7199
expose 9160
expose 9042

cmd /opt/cassandra/bin/start

