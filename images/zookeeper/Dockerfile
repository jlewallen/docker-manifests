FROM jlewallen/tomcat

MAINTAINER Jacob Lewallen

RUN mkdir -p /opt /svr
RUN cd /opt && wget http://apache.mesi.com.ar/zookeeper/zookeeper-3.4.5/zookeeper-3.4.5.tar.gz
RUN cd /opt && tar zxf zookeeper-*.tar.gz && rm /opt/*.tar.gz
RUN mv /opt/zookeeper-* /opt/zookeeper
RUN mkdir -p /opt/zookeeper/conf
RUN cp /opt/zookeeper/conf/zoo_sample.cfg /opt/zookeeper/conf/zoo.cfg

RUN mkdir /opt/zkdata /opt/zklogs
ADD exhibitor.war /opt/tomcat/webapps/exhibitor.war
ADD exhibitor.properties /opt/exhibitor.properties

EXPOSE 8888 2181 2888 3888

CMD "/opt/tomcat/bin/catalina.sh run"
