# Simulator setup
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Path to source directory
SRC_DIR = $(CURDIR)/../../unic_cass_wrapper_user_project/fft16_project/src

# Sources
VERILOG_SOURCES += $(SRC_DIR)/btfly_2.v

# DUT settings
TOPLEVEL = btfly_2
MODULE = btfly_2_tb

# Cocotb standard rules
include $(shell cocotb-config --makefiles)/Makefile.sim
