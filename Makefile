.PHONY: bash
bash:
	docker-compose run --rm scanblog bash

.PHONY: build
build:
	docker-compose buld scanblog

.PHONY: manage.py
manage.py:
	docker-compose run --rm scanblog ./scanblog/manage.py $(ARGS)

.PHONY: test
test:
	docker-compose run --rm selenium ./scanblog/manage.py test $(ARGS)

