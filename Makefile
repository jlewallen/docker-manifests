zookeeper:		
		(echo zookeeper && cd images/zookeeper && docker build -t jlewallen/zookeeper . ) ; \

all:
	docker pull ubuntu
	for a in base tomcat eureka nginx cassandra zookeeper; do \
		(echo $$a && cd images/$$a && docker build -t jlewallen/$$a . ) ; \
	done
