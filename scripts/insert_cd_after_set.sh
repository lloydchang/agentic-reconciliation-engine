#!/bin/bash

# filename: insert_cd_after_set.sh

set -euo pipefail

# This script safely inserts `cd $(dirname $0)` after `set -euo pipefail`
# in all shell scripts in the current repository, avoiding duplicates and preserving sourced scripts.
# Updated for macOS compatibility without requiring Bash 4.

find .. -type f -name "*.sh" | while read -r file; do
    [ -f "$file" ] || continue

    # Check if the script already contains `cd $(dirname $0)` after `set -euo pipefail`
    if grep -q '^set -euo pipefail$' "$file"; then
        if grep -A1 '^set -euo pipefail$' "$file" | grep -q 'cd \$\(dirname \$0\)'; then
            echo "Skipping $file: already has cd line"
            continue
        fi

        # Insert `cd $(dirname $0)` after `set -euo pipefail`
        tmpfile="$(mktemp)"
        awk '/^set -euo pipefail$/ && !added {print; print "cd $(dirname $0)"; added=1; next} {print}' "$file" > "$tmpfile" && mv "$tmpfile" "$file"
        echo "Patched $file"
    else
        echo "Skipping $file: no set -euo pipefail line"
    fi

done

echo "All eligible shell scripts processed."

