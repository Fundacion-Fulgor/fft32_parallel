# Simulator setup
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

PROJECT_DIR = $(CURDIR)/../..
# Deliberately not PDK_ROOT: that name is often already set in the environment
PDK_DIR    ?= $(PROJECT_DIR)/IHP-Open-PDK
STDCELL_DIR = $(PDK_DIR)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog
RUN_TAG    ?= user_project_run
NETLIST    ?= $(PROJECT_DIR)/unic_cass_wrapper_user_project/fft16_project/runs/$(RUN_TAG)/final/nl/fft16_project.nl.v

# The IHP cell models drive their flip-flops from delayed_* wires that only the
# specify block produces, and Icarus does not implement that, so every output
# would stay X. prepare_models.py rewrites those wires as direct aliases.
SIM_MODELS = $(CURDIR)/sim_build/sg13g2_stdcell_sim.v

# Standard cell models, the synthesised netlist and the port adapter
VERILOG_SOURCES += $(STDCELL_DIR)/sg13g2_udp.v
VERILOG_SOURCES += $(SIM_MODELS)
VERILOG_SOURCES += $(NETLIST)
VERILOG_SOURCES += $(CURDIR)/gls_top.v

# The bring-up testbench is reused as is; it only ever touches ports
export PYTHONPATH := $(CURDIR)/../top_fft16_bringup:$(PROJECT_DIR)/model:$(PYTHONPATH)

TOPLEVEL = gls_top
MODULE   = top_fft16_bringup_tb

# Cocotb standard rules
include $(shell cocotb-config --makefiles)/Makefile.sim

$(SIM_MODELS): $(STDCELL_DIR)/sg13g2_stdcell.v prepare_models.py
	@mkdir -p $(dir $@)
	python3 $(CURDIR)/prepare_models.py $< $@

sim_build/sim.vvp: $(SIM_MODELS)
