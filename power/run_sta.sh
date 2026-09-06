#!/usr/bin/env bash
set -e

SHARED=/home/designer/shared
POWER_DIR=$SHARED/power
STA=${STA:-$(ls -d /opt/openroad/*/bin/sta 2>/dev/null | head -1)}
[ -x "$STA" ] || { echo "OpenSTA not found in this image" >&2; exit 1; }

export RUN_DIR=${RUN_DIR:-$SHARED/unic_cass_wrapper_user_project/fft16_project/runs/${RUN_TAG:-user_project_run}}
export DESIGN_NAME=${DESIGN_NAME:-fft16_project}
export CORNER=${CORNER:-nom_typ_1p20V_25C}
export PDK_DIR=${PDK_DIR:-$SHARED/IHP-Open-PDK}
POWER_MODE=${POWER_MODE:-fft}
export VCD_FILE=${VCD_FILE:-$POWER_DIR/sim_build/power_$POWER_MODE.vcd}
export VCD_SCOPE=${VCD_SCOPE:-power_top/u_$DESIGN_NAME}
export CLOCK_PERIOD=${CLOCK_PERIOD:-20}

"$STA" -no_init -exit "$POWER_DIR/power.tcl"
