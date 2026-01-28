# Simulator setup
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# PATH to sources
SRC_DIR = $(PWD)/../../unic_cass_wrapper_user_project/fft32_project/src

# Sources
VERILOG_SOURCES += $(SRC_DIR)/fft8.v
VERILOG_SOURCES += $(SRC_DIR)/mdc8p_stage1.v
VERILOG_SOURCES += $(SRC_DIR)/mdc8p_stage2.v
VERILOG_SOURCES += $(SRC_DIR)/mdc8p_stage3.v
VERILOG_SOURCES += $(SRC_DIR)/btfly_2.v
VERILOG_SOURCES += $(SRC_DIR)/xfft_cell.v
VERILOG_SOURCES += $(SRC_DIR)/ds_switch.v
# shift_r2.v is not instantiated in fft8.v but good to have
VERILOG_SOURCES += $(SRC_DIR)/shift_r2.v 

# DUT settings
TOPLEVEL = fft8
MODULE = fft8_tb

# Cocotb standard rules
include $(shell cocotb-config --makefiles)/Makefile.sim