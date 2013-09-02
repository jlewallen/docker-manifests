from jlewallen/tomcat

maintainer Jacob Lewallen

run echo eureka.numberRegistrySyncRetries=0 >> /opt/tomcat/conf/catalina.properties
run echo eureka.enableSelfPreservation=false >> /opt/tomcat/conf/catalina.properties
add eureka-server-1.1.113-SNAPSHOT.war /opt/tomcat/webapps/eureka.war
add server.xml /opt/tomcat/conf/server.xml

expose 80

entrypoint ["/opt/tomcat/bin/start"]

