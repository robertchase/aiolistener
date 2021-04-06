.PHONY: shell lint test

ifeq ($(GIT),)
  GIT := $(HOME)/git
endif

IMAGE := base-python
NAME := aiolistener

NET := --net test
MOUNT := /opt/git
VOLUMES := -v=$(GIT):$(MOUNT)
WORKING := -w $(MOUNT)/$(NAME)
PYTHONPATH := -e PYTHONPATH=.

DOCKER := docker run --rm -it $(VOLUMES) $(PYTHONPATH) $(WORKING) $(NET) $(IMAGE)

shell:
	$(DOCKER) bash

lint:
	$(DOCKER) pylint $(NAME)

test:
	$(DOCKER) pytest
