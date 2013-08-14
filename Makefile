nginx:
	for a in nginx; do \
		(echo $$a && cd images/$$a && docker build -t jlewallen/$$a . ) ; \
	done

all:
	for a in base tomcat eureka nginx cassandra; do \
		(echo $$a && cd images/$$a && docker build -t jlewallen/$$a . ) ; \
	done
