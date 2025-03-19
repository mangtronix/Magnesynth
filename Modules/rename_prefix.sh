#!/bin/bash

for file in [A-Z]*[0-9]*; do
    if [[ -f "$file" ]]; then
        # Find the position of the first digit
        prefix=$(echo "$file" | sed -E 's/([A-Z]+)[0-9].*/\1/')
        rest="${file#$prefix}"
        newname="${prefix}-${rest}"
        
        # Only rename if the file doesn't already have a dash after the prefix
        if [[ "$file" != "$newname" ]]; then
            mv "$file" "$newname"
            echo "Renamed: $file to $newname"
        else
            echo "Skipped: $file (already in correct format)"
        fi
    fi
done

