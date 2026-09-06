# Simulator setup
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Path to source directory
SRC_DIR = $(PWD)/../../unic_cass_wrapper_user_project/fft16_project/src

# Sources
VERILOG_SOURCES += $(SRC_DIR)/fft4_mul.v
VERILOG_SOURCES += $(SRC_DIR)/clip_round.v

# DUT settings
TOPLEVEL = fft4_mul
MODULE = fft4_mul_tb

# Cocotb standard rules
include $(shell cocotb-config --makefiles)/Makefile.sim
