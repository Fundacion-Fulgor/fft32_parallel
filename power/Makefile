# Simulator setup
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

PROJECT_DIR = $(CURDIR)/..
PDK_DIR    ?= $(PROJECT_DIR)/IHP-Open-PDK
STDCELL_DIR = $(PDK_DIR)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog
RUN_TAG    ?= user_project_run
RUN_DIR    ?= $(PROJECT_DIR)/unic_cass_wrapper_user_project/fft16_project/runs/$(RUN_TAG)
DESIGN_NAME ?= fft16_project
CORNER     ?= nom_typ_1p20V_25C
CLOCK_PERIOD ?= 20

NETLIST  = $(RUN_DIR)/final/nl/$(DESIGN_NAME).nl.v
POWER_MODE ?= fft
VCD_FILE  ?= $(CURDIR)/sim_build/power_$(POWER_MODE).vcd
VCD_SCOPE ?= power_top/u_$(DESIGN_NAME)
REPORT    ?= $(CURDIR)/power.rpt
POWER_BLOCKS ?= 4

# OpenSTA lives in the tools container, cocotb lives on the host. If sta is on
# PATH the report runs locally, otherwise it is delegated to the image.
STA_LOCAL := $(shell command -v sta 2>/dev/null)
IMAGE     ?= isaiassh/unic-cass-tools:1.2.3

# Keeps the OpenSTA start-up banner out of the report, warnings included.
BANNER = grep -v -E '^(OpenSTA [0-9]|License GPLv3|This is free software|under certain conditions|This program comes with)'

# Same model fixup the gate level suite needs: the IHP cell models take their
# flip-flop inputs from delayed_* wires that only the specify block drives, and
# Icarus does not implement that, so every output would stay X.
PREPARE_MODELS = $(PROJECT_DIR)/tests/gls/prepare_models.py
SIM_MODELS     = $(CURDIR)/sim_build/sg13g2_stdcell_sim.v

VERILOG_SOURCES += $(STDCELL_DIR)/sg13g2_udp.v
VERILOG_SOURCES += $(SIM_MODELS)
VERILOG_SOURCES += $(NETLIST)
VERILOG_SOURCES += $(CURDIR)/power_top.v

# The activity simulation runs zero delay: the delayed_* aliases needed to make
# the IHP models work under Icarus are incompatible with the timing checks that
# SDF annotation activates. OpenSTA reads the SDF itself, and that is what the
# power numbers are derived from.
PLUSARGS += +vcd=$(VCD_FILE)

export POWER_MODE
export POWER_BLOCKS

export PYTHONPATH := $(PROJECT_DIR)/tests/top_fft16_bringup:$(PROJECT_DIR)/model:$(PYTHONPATH)

TOPLEVEL = power_top
MODULE   = power_tb

.PHONY: power report clean-power

power: sim report

# OpenSTA derives the activity duration from the VCD time stamps, so the trace
# is shifted to start at zero: what is left is exactly the streaming window.
report: $(VCD_FILE)
	@python3 $(CURDIR)/rebase_vcd.py $(VCD_FILE) --mode $(POWER_MODE) \
	  --corner $(CORNER) --clock-ns $(CLOCK_PERIOD) --blocks $(POWER_BLOCKS) \
	  --netlist $(DESIGN_NAME).nl.v --run-tag $(RUN_TAG) > $(REPORT)
	@cat $(REPORT)
ifeq ($(STA_LOCAL),)
	docker run --rm \
	  --mount type=bind,source=$(abspath $(PROJECT_DIR)),target=/home/designer/shared \
	  -e USER_ID=$(shell id -u) -e USER_GROUP=$(shell id -g) \
	  -e RUN_TAG=$(RUN_TAG) -e DESIGN_NAME=$(DESIGN_NAME) -e CORNER=$(CORNER) \
	  -e CLOCK_PERIOD=$(CLOCK_PERIOD) -e POWER_MODE=$(POWER_MODE) \
	  $(IMAGE) /home/designer/shared/power/run_sta.sh \
	  2>&1 | $(BANNER) | tee -a $(REPORT)
else
	RUN_DIR=$(RUN_DIR) DESIGN_NAME=$(DESIGN_NAME) CORNER=$(CORNER) \
	PDK_DIR=$(PDK_DIR) VCD_FILE=$(VCD_FILE) VCD_SCOPE=$(VCD_SCOPE) \
	CLOCK_PERIOD=$(CLOCK_PERIOD) \
	$(STA_LOCAL) -no_init -exit $(CURDIR)/power.tcl \
	  2>&1 | $(BANNER) | tee -a $(REPORT)
endif

clean-power:
	rm -rf sim_build results.xml __pycache__ power.rpt

# Cocotb standard rules, only when cocotb is present: the report target must
# still work inside the tools container, which has OpenSTA but not cocotb.
COCOTB_MAKEFILES := $(shell cocotb-config --makefiles 2>/dev/null)
ifneq ($(COCOTB_MAKEFILES),)
include $(COCOTB_MAKEFILES)/Makefile.sim
else
sim:
	@echo "cocotb is not installed here: run 'make sim' where cocotb is available." >&2
	@false
endif

$(SIM_MODELS): $(STDCELL_DIR)/sg13g2_stdcell.v $(PREPARE_MODELS)
	@mkdir -p $(dir $@)
	python3 $(PREPARE_MODELS) $< $@

sim_build/sim.vvp: $(SIM_MODELS)
