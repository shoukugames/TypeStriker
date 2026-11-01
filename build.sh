#!/usr/bin/env bash
# Builds both installers into dist/
set -euo pipefail
cd "$(dirname "$0")"
packaging/build_linux.sh
packaging/build_windows.sh
