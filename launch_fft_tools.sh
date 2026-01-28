#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
# Description:
#   Syncs 'fft32_parallel' to Docker shared folder.
#   Skips copying heavy folders (IHP-Open-PDK, librelane) 
#   if they already exist in the destination.
#
# Usage:
#   ./launch_fft_tools.sh
# ------------------------------------------------------------------------------

# ==============================================================================
# CONFIGURATION
# ==============================================================================

DEFAULT_SRC="/mnt/c/Users/fedef/Documents/Maestria/UNIC-CASS/fft32_parallel"
PROJECT_SRC="${PROJECT_SRC:-$DEFAULT_SRC}"

PARENT_DIR="$(dirname "$PROJECT_SRC")"
if [[ -d "$PARENT_DIR/uniccass-icdesign-tools" ]]; then
    TOOLS_DIR="${TOOLS_DIR:-$PARENT_DIR/uniccass-icdesign-tools}"
else
    TOOLS_DIR="${TOOLS_DIR:-$PARENT_DIR/uniccass-icdesign-tools}"
fi

SHARED_DIR="${SHARED_DIR:-$TOOLS_DIR/shared_xserver}"
DEST_DIR="${DEST_DIR:-$SHARED_DIR/FFT/fft32_parallel}"

CONTAINER_SHARED_ROOT="/home/designer/shared"
DEST_IN_CONTAINER="$CONTAINER_SHARED_ROOT/FFT/fft32_parallel"

START_DOCKER="${START_DOCKER:-1}"
CLEAN_OLD_CONTAINERS="${CLEAN_OLD_CONTAINERS:-1}"

# ==============================================================================
# CHECKS
# ==============================================================================

if [[ ! -d "$PROJECT_SRC" ]]; then
  echo "ERROR: Source repository not found at: $PROJECT_SRC"
  exit 1
fi
if [[ ! -d "$TOOLS_DIR" ]]; then
  echo "ERROR: Tools directory not found at: $TOOLS_DIR"
  exit 1
fi
if ! command -v rsync >/dev/null 2>&1; then
  echo "ERROR: 'rsync' is not installed."
  exit 1
fi

mkdir -p "$DEST_DIR"

# ==============================================================================
# SMART SYNC (The optimization)
# ==============================================================================

echo "==> Starting Smart Sync..."
echo "    From: $PROJECT_SRC"
echo "    To:   $DEST_DIR"

# 1. HEAVY FILES CHECK: Copy ONLY if they don't exist yet
#    We check for 'IHP-Open-PDK' and 'librelane' explicitly.

if [[ ! -d "$DEST_DIR/IHP-Open-PDK" ]]; then
    echo "    [First Run] Copying IHP-Open-PDK (This takes time)..."
    rsync -a "$PROJECT_SRC/IHP-Open-PDK" "$DEST_DIR/"
else
    echo "    [Skip] IHP-Open-PDK already exists. Skipping copy."
fi

if [[ ! -d "$DEST_DIR/librelane" ]]; then
    echo "    [First Run] Copying librelane (This takes time)..."
    rsync -a "$PROJECT_SRC/librelane" "$DEST_DIR/"
else
    echo "    [Skip] librelane already exists. Skipping copy."
fi

# 2. SOURCE CODE SYNC: Fast sync for everything else
#    Crucially, we EXCLUDE the heavy folders here so --delete doesn't wipe them out
#    if rsync thinks they are different, and so we don't scan them again.

echo "    [Sync] Updating source code (.v, .json, scripts)..."
rsync -av --delete \
  --exclude '.git/' \
  --exclude '.github/' \
  --exclude 'runs/' \
  --exclude 'build/' \
  --exclude '__pycache__/' \
  --exclude '*.vcd' \
  --exclude '*.vvp' \
  --exclude '.pytest_cache/' \
  --exclude 'IHP-Open-PDK/' \
  --exclude 'librelane/' \
  "$PROJECT_SRC/" "$DEST_DIR/"

# ==============================================================================
# HELPER SCRIPT GENERATION
# ==============================================================================

cat > "$DEST_DIR/run_librelane.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

DESIGN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_CONFIG="$DESIGN_DIR/unic_cass_wrapper_user_project/fft32_project/src/config.json"
CONFIG_PATH="${1:-$DEFAULT_CONFIG}"

PDK_NAME="${PDK_NAME:-${PDK:-ihp-sg13g2}}"
THREADS="${THREADS:-$(nproc 2>/dev/null || echo 4)}"

export OMP_NUM_THREADS="$THREADS"
export OPENROAD_NUM_THREADS="$THREADS"
export KLAYOUT_DRC_THREADS="$THREADS"

echo "[Wrapper] PDK: $PDK_NAME"
echo "[Wrapper] Cfg: $CONFIG_PATH"

if [[ "$CONFIG_PATH" == -* ]]; then
    SET_CONFIG="$DEFAULT_CONFIG"
    ARGS=("$@")
else
    SET_CONFIG="$CONFIG_PATH"
    if [[ "$1" == "$CONFIG_PATH" ]]; then shift; fi
    ARGS=("$@")
fi

if librelane --help 2>/dev/null | grep -q -- "--threads"; then
  exec librelane --pdk "$PDK_NAME" --design-dir "$DESIGN_DIR" --threads "$THREADS" "$SET_CONFIG" "${ARGS[@]}"
else
  exec librelane --pdk "$PDK_NAME" --design-dir "$DESIGN_DIR" "$SET_CONFIG" "${ARGS[@]}"
fi
EOF
chmod +x "$DEST_DIR/run_librelane.sh"

echo "==> Sync complete."
echo "    Container Path: $DEST_IN_CONTAINER"
echo ""

# ==============================================================================
# START DOCKER
# ==============================================================================

if [[ "$START_DOCKER" == "1" ]]; then
  if [[ "$CLEAN_OLD_CONTAINERS" == "1" ]]; then
    existing="$(docker ps -a --format '{{.Names}}' | grep -E '^unic-cass-tools-' || true)"
    if [[ -n "$existing" ]]; then
      echo "==> Removing stale containers..."
      echo "$existing" | xargs docker rm -f >/dev/null 2>&1 || true
    fi
  fi

  echo "==> Starting Docker environment (make start)..."
  cd "$TOOLS_DIR"
  make start
fi