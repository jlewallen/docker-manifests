FROM jlewallen/base

MAINTAINER Jacob Lewallen

ADD startup /docker/startup/00-tomcat
RUN chmod 755 /docker/startup/00-tomcat

EXPOSE 8080

CMD "/opt/tomcat/bin/catalina.sh run"

