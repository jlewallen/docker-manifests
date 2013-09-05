FROM jlewallen/tomcat

MAINTAINER Jacob Lewallen

RUN echo eureka.numberRegistrySyncRetries=0 >> /opt/tomcat/conf/catalina.properties
RUN echo eureka.enableSelfPreservation=false >> /opt/tomcat/conf/catalina.properties
ADD eureka-server-1.1.113-SNAPSHOT.war /opt/tomcat/webapps/eureka.war
ADD server.xml /opt/tomcat/conf/server.xml

EXPOSE 80

CMD "/opt/tomcat/bin/catalina.sh run"

