
all:
	docker pull ubuntu
	for a in base tomcat eureka nginx cassandra zookeeper; do \
    (echo $$a && docker rmi jlewallen/$$a) ;\
		(echo $$a && cd images/$$a && docker build -t jlewallen/$$a . ) ; \
	done

base:		
		(echo base && cd images/base && docker build -t jlewallen/base . ) ; \

nginx: base
		(echo nginx && cd images/nginx && docker build -t jlewallen/nginx . ) ; \

zookeeper: base
		(echo zookeeper && cd images/zookeeper && docker build -t jlewallen/zookeeper . ) ; \

cassandra: base
		(echo cassandra && cd images/cassandra && docker build -t jlewallen/cassandra . ) ; \

tomcat: base
		docker rmi jlewallen/tomcat
		(echo tomcat && cd images/tomcat && docker build -t jlewallen/tomcat . ) ; \

gerrit: base
		docker rmi jlewallen/gerrit
		(echo gerrit && cd images/gerrit && docker build -t jlewallen/gerrit . ) ; \
