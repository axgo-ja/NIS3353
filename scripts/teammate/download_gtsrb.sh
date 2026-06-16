#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${REPO_ROOT}/data"
TMP_DIR="${DATA_DIR}/gtsrb_tmp"
READY_MARKER="${DATA_DIR}/GTSRB/.ready"

mkdir -p "${DATA_DIR}" "${TMP_DIR}"

if [[ -f "${READY_MARKER}" ]]; then
  echo "GTSRB is already prepared."
  exit 0
fi

declare -A URLS=(
  ["GTSRB_Final_Training_Images.zip"]="https://sid.erda.dk/public/archives/daaeac0d7ce1152aea9b61d9f1e19370/GTSRB_Final_Training_Images.zip"
  ["GTSRB_Final_Test_Images.zip"]="https://sid.erda.dk/public/archives/daaeac0d7ce1152aea9b61d9f1e19370/GTSRB_Final_Test_Images.zip"
  ["GTSRB_Final_Test_GT.zip"]="https://sid.erda.dk/public/archives/daaeac0d7ce1152aea9b61d9f1e19370/GTSRB_Final_Test_GT.zip"
)

for file in "${!URLS[@]}"; do
  wget -c "${URLS[$file]}" -O "${DATA_DIR}/${file}"
done

rm -rf "${TMP_DIR}" "${DATA_DIR}/GTSRB"
mkdir -p "${TMP_DIR}" "${DATA_DIR}/GTSRB/Train" "${DATA_DIR}/GTSRB/Test"

extract_zip() {
  local zip_path="$1"
  local dest_dir="$2"
  python - "${zip_path}" "${dest_dir}" <<'PY'
import sys
import zipfile
from pathlib import Path

zip_path = Path(sys.argv[1])
dest_dir = Path(sys.argv[2])
dest_dir.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(zip_path) as zf:
    zf.extractall(dest_dir)
PY
}

extract_zip "${DATA_DIR}/GTSRB_Final_Training_Images.zip" "${TMP_DIR}/Train"
extract_zip "${DATA_DIR}/GTSRB_Final_Test_Images.zip" "${TMP_DIR}/Test"
extract_zip "${DATA_DIR}/GTSRB_Final_Test_GT.zip" "${DATA_DIR}/GTSRB/Test"

mv "${TMP_DIR}/Train/GTSRB/Final_Training/Images/"* "${DATA_DIR}/GTSRB/Train/"
mv "${TMP_DIR}/Test/GTSRB/Final_Test/Images/"* "${DATA_DIR}/GTSRB/Test/"

rm -rf "${TMP_DIR}"
touch "${READY_MARKER}"
echo "GTSRB is available under ${DATA_DIR}/GTSRB"
