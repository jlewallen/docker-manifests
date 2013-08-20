base:		
		(echo base && cd images/base && docker build -t jlewallen/base . ) ; \

zookeeper: base
		(echo zookeeper && cd images/zookeeper && docker build -t jlewallen/zookeeper . ) ; \

cassandra: base
		(echo cassandra && cd images/cassandra && docker build -t jlewallen/cassandra . ) ; \

all:
	docker pull ubuntu
	for a in base tomcat eureka nginx cassandra zookeeper; do \
		(echo $$a && cd images/$$a && docker build -t jlewallen/$$a . ) ; \
	done
