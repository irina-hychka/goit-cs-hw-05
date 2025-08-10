#!/bin/bash

# Website availability checker
# Uses curl to request each URL and logs whether it's UP (HTTP 200) or DOWN.

# --- Config ---
WEBSITES=("https://google.com" "https://facebook.com" "https://twitter.com")
LOG_FILE="website_status.log"

# Start fresh each run (comment this out if you prefer appending)
: > "$LOG_FILE"

# --- Check loop ---
for url in "${WEBSITES[@]}"; do
  # -sS: silent but show errors; -L: follow redirects
  # --connect-timeout 5: fail fast on DNS/connection issues
  # --max-time 10: total request ceiling
  # -o /dev/null: discard body; -w "%{http_code}": print only status
  http_code=$(curl -sS -L --connect-timeout 5 --max-time 10 -o /dev/null -w "%{http_code}" "$url" 2>>"$LOG_FILE")

  timestamp=$(date +"%Y-%m-%d %H:%M:%S")

  if [ "$http_code" -eq 200 ]; then
    echo "[$timestamp] [<$url>](<$url>) is UP" >> "$LOG_FILE"
  else
    # curl returns 000 on DNS/timeout/etc
    echo "[$timestamp] [<$url>](<$url>) is DOWN (code: $http_code)" >> "$LOG_FILE"
  fi
done

echo "Results have been written to $LOG_FILE"
