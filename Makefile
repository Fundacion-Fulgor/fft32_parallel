PROJECT_DIR = $(shell pwd)
LIBRELANE_DIR ?= $(PROJECT_DIR)/librelane
designs = fft16_project

.PHONY: setup
setup:
	git submodule update --init --recursive

.PHONY: librelane
librelane: unic_cass_wrapper_user_project unic_cass_wrapper copy_results

.PHONY: unic_cass_wrapper_user_project
unic_cass_wrapper_user_project:
	$(MAKE) -C unic_cass_wrapper_user_project $(designs)

.PHONY: unic_cass_wrapper
unic_cass_wrapper:
	$(MAKE) -C unic_cass_wrapper

.PHONY: copy_results
copy_results:
	cp -r unic_cass_wrapper/final final/
