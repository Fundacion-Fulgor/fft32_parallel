# Simulator setup
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Path to source directory
SRC_DIR = $(PWD)/../../unic_cass_wrapper_user_project/fft16_project/src

# Sources
VERILOG_SOURCES += $(SRC_DIR)/spi_slave_mode0.v

# DUT settings
TOPLEVEL = spi_slave_mode0
MODULE = spi_slave_mode0_tb

# Cocotb standard rules
include $(shell cocotb-config --makefiles)/Makefile.sim
