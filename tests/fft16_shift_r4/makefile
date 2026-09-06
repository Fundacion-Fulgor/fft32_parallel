# Simulator setup
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Path to source directory
SRC_DIR = $(CURDIR)/../../unic_cass_wrapper_user_project/fft16_project/src

# Sources
VERILOG_SOURCES += $(SRC_DIR)/fft16_shift_r4.v

# DUT settings
TOPLEVEL = fft16_shift_r4
MODULE = fft16_shift_r4_tb

# Cocotb standard rules
include $(shell cocotb-config --makefiles)/Makefile.sim
