# Simulator setup
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Path to source directory
SRC_DIR = $(PWD)/../../unic_cass_wrapper_user_project/fft16_project/src

# Sources
VERILOG_SOURCES += $(SRC_DIR)/ds_switch.v

# DUT settings
TOPLEVEL = ds_switch
MODULE = ds_switch_tb

# Cocotb standard rules
include $(shell cocotb-config --makefiles)/Makefile.sim
