#!/usr/bin/env bash
# Cuts and restores the network of ONE pump (takes it off the Docker network "station").
#   ./demo/network.sh off pump-03   pump 3 keeps listening; its events wait in the nucleus queue
#   ./demo/network.sh on  pump-03   the network is back; the queued events reach the cloud
set -euo pipefail
STATE="${1:?off | on}"
P="${2:?pump (pump-01 … pump-05)}"
[[ "$P" =~ ^pump-0[1-5]$ ]] || { echo "unknown pump: $P  (pump-01 … pump-05)"; exit 1; }

case "$STATE" in
  off) docker network disconnect station "$P"
       echo "▶ $P offline  $(date +%H:%M:%S)" ;;
  on)  docker network connect station "$P"
       echo "▶ $P back online  $(date +%H:%M:%S)" ;;
  *)   echo "usage: $0 <off|on> <pump>"; exit 1 ;;
esac
