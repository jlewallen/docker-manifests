from jlewallen/tomcat

maintainer Jacob Lewallen

run mkdir -p /opt /svr
run cd /opt && wget http://mirror.tcpdiag.net/apache/cassandra/2.0.0/apache-cassandra-2.0.0-bin.tar.gz
run cd /opt && tar zxf apache-cassandra-*.tar.gz
run rm /opt/*.tar.gz
run mv /opt/apache-cassandra-* /opt/cassandra
add cassandra-env.sh /opt/cassandra/conf/cassandra-env.sh
add cassandra.yaml /opt/cassandra/conf/cassandra.yaml

add start /opt/cassandra/bin/start
run chmod 755 /opt/cassandra/bin/start

expose 7000
expose 7001
expose 7199
expose 8080
expose 8888
expose 9160
expose 9042

cmd "/opt/cassandra/bin/start"
