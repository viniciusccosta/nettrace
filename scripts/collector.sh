#!/bin/bash

# --- Usage ---
usage() {
    echo "Usage: $0 -n <network_cidr> [-o <output_dir>]"
    echo "  -n  Network to scan, e.g. 192.168.1.0/24  (required)"
    echo "  -o  Directory to save CSV files            (default: \$HOME/logs_rede)"
    exit 1
}

# --- Parse arguments ---
NETWORK=""
LOG_DIR="$HOME/logs_rede"

while getopts "n:o:" opt; do
    case "$opt" in
        n) NETWORK="$OPTARG" ;;
        o) LOG_DIR="$OPTARG" ;;
        *) usage ;;
    esac
done

[ -z "$NETWORK" ] && usage

# --- Lock: prevent overlapping runs if nmap takes longer than the cron interval ---
LOCK_FILE="/tmp/collector_nettrace.lock"
if [ -e "$LOCK_FILE" ] && kill -0 "$(cat "$LOCK_FILE")" 2>/dev/null; then
    echo "Already running (PID $(cat "$LOCK_FILE")), exiting." >&2
    exit 1
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# --- Config ---
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
CSV_FILE="$LOG_DIR/scan_$(date '+%Y-%m-%d').csv"

mkdir -p "$LOG_DIR"

# --- Header: write only if file does not exist yet ---
if [ ! -f "$CSV_FILE" ]; then
    echo "Timestamp,IP,MAC" > "$CSV_FILE"
fi

# --- Scan and append results ---
nmap -sn -PR "$NETWORK" | awk -v ts="$TIMESTAMP" '
  /^Nmap scan report for / { ip = $NF; next }
  /^MAC Address: / {
    mac = $3;
    print ts "," ip "," mac
  }
' >> "$CSV_FILE"

# --- To schedule this script (requires root for nmap -PR) ---
# sudo crontab -e
# Add: */10 * * * * /full/path/to/collector.sh -n 192.168.1.0/24