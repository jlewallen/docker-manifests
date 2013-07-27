from ubuntu

maintainer Jacob Lewallen

run echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list
run apt-get update
run apt-get install -y vim wget curl tmux git openjdk-6-jdk nginx # libtcnative-1
run mkdir -p /opt
run cd /opt && wget http://apache.spinellicreations.com/tomcat/tomcat-7/v7.0.42/bin/apache-tomcat-7.0.42.tar.gz
run cd /opt && tar zxf apache-tomcat-*.tar.gz
run rm /opt/*.tar.gz
run mv /opt/apache-tomcat-* /opt/tomcat

