#!/bin/bash

set -euo pipefail
cd $(dirname $0)

cd "$(dirname "$0")"

# filename: ensure_shell_safety.sh

# This script ensures every shell script in the repository has `set -euo pipefail`.
# If missing, it adds both `set -euo pipefail` and `cd $(dirname $0)` after the shebang.
# Also inserts `cd $(dirname $0)` if only `set -euo pipefail` is present.
# Prevents duplicate cd lines anywhere in the header.
# macOS compatible version.

find .. -type f -name "*.sh" | while read -r file; do
    [ -f "$file" ] || continue

    tmpfile="$(mktemp)"

    # Read header lines until first non-comment, non-empty line
    header=$(awk '/^[[:space:]]*$/ {print; next} /^[[:space:]]*#/ {print; next} {exit}' "$file")

    # Detect shebang
    first_line=$(head -n 1 "$file")
    has_shebang=0
    if [[ "$first_line" == \#!* ]]; then
        has_shebang=1
    fi

    # Check if set -euo pipefail exists anywhere
    has_set_line=$(grep -n '^ *set -euo pipefail *$' "$file" | cut -d: -f1)
    # Check if cd line exists anywhere in header (before first non-comment code)
    has_cd_line=$(awk '/^[[:space:]]*$/ {next} /^[[:space:]]*#/ {print; next} {exit}' "$file" | grep -q 'cd \$\(dirname \$0\)' && echo 1 || echo 0)

    if [ -n "$has_set_line" ]; then
        # set line exists, maybe add cd
        if [ "$has_cd_line" -eq 1 ]; then
            echo "Skipping $file: already has set -euo pipefail and cd line"
            continue
        fi
        # Insert cd after set line
        awk '/^ *set -euo pipefail *$/ && !added {print; print "cd $(dirname $0)"; added=1; next} {print}' "$file" > "$tmpfile" && mv "$tmpfile" "$file"
        echo "Patched $file: added cd line after existing set -euo pipefail"
    else
        # set line missing, insert after shebang if exists, else top
        if [ $has_shebang -eq 1 ]; then
            { head -n 1 "$file"; echo -e "set -euo pipefail\ncd \$(dirname \$0)"; tail -n +2 "$file"; } > "$tmpfile" && mv "$tmpfile" "$file"
        else
            { echo -e "set -euo pipefail\ncd \$(dirname \$0)"; cat "$file"; } > "$tmpfile" && mv "$tmpfile" "$file"
        fi
        echo "Patched $file: added set -euo pipefail and cd line"
    fi

done

echo "All shell scripts checked and patched as needed."
