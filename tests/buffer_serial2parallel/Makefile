SIM ?= icarus
TOPLEVEL_LANG ?= verilog

SRC_DIR = $(PWD)/../../unic_cass_wrapper_user_project/fft32_project/src

VERILOG_SOURCES += $(SRC_DIR)/buffer_serial2parallel.v

TOPLEVEL = buffer_serial2parallel
MODULE   = buffer_serial2parallel_tb

include $(shell cocotb-config --makefiles)/Makefile.sim