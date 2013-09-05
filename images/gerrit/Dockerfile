FROM jlewallen/tomcat

MAINTAINER Jacob Lewallen

RUN rm -rf /opt/tomcat/webapps/*
ADD gerrit-2.6.war /opt/tomcat/webapps/gerrit.war
ADD context.xml /opt/tomcat/conf/context.xml
ADD gerrit.config /gerrit/site/etc/gerrit.config

RUN adduser --gecos "Gerrit" --disabled-password gerrit
RUN java -jar /opt/tomcat/webapps/gerrit.war init --batch -d /gerrit/site
RUN echo "GERRIT_SITE=/gerrit/site/" >> /opt/tomcat/conf/catalina.properties

EXPOSE 8080
EXPOSE 29418

CMD "/opt/tomcat/bin/catalina.sh run"

