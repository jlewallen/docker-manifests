from jlewallen/base

maintainer Jacob Lewallen

run mkdir -p /opt /svr
run cd /opt && wget http://apache.mesi.com.ar/zookeeper/zookeeper-3.4.5/zookeeper-3.4.5.tar.gz
run cd /opt && tar zxf zookeeper-*.tar.gz
run rm /opt/*.tar.gz
run mv /opt/zookeeper-* /opt/zookeeper
add start /opt/zookeeper/bin/start
run chmod 755 /opt/zookeeper/bin/start
run mkdir -p /opt/zookeeper/conf
run cp /opt/zookeeper/conf/zoo_sample.cfg /opt/zookeeper/conf/zoo.cfg

expose 2181

entrypoint [ "/opt/zookeeper/bin/start" ]

