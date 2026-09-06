SIM ?= icarus
TOPLEVEL_LANG ?= verilog

SRC_DIR = $(CURDIR)/../../unic_cass_wrapper_user_project/fft16_project/src

VERILOG_SOURCES += $(SRC_DIR)/debug_system.v
VERILOG_SOURCES += $(SRC_DIR)/debug_unit.v
VERILOG_SOURCES += $(SRC_DIR)/spi_slave_mode0.v
VERILOG_SOURCES += $(SRC_DIR)/cdc_snapshot.v

TOPLEVEL = debug_system
MODULE   = debug_system_tb

include $(shell cocotb-config --makefiles)/Makefile.sim
