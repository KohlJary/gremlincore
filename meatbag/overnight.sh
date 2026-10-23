#!/usr/bin/env bash
# Overnight chain after the main local pass: retry failed rows, sort the
# gremlin flags, then build the open corpus (the eval wall), then write
# the morning report. All local, no paid API spend. Run from the agent's
# home (or set GREMLIN_HOME). Log: data/overnight.log
set -u
cd "${GREMLIN_HOME:-$PWD}"
mkdir -p data
log=data/overnight.log
echo "[$(date)] waiting for the main pass" >> $log
while pgrep -f "meatbag mine moves" > /dev/null; do sleep 60; done
echo "[$(date)] main pass done: $(wc -l < data/moves_raw.jsonl) rows" >> $log
meatbag mine moves >> data/moves_retry.log 2>&1
echo "[$(date)] retry done: $(wc -l < data/moves_raw.jsonl) rows" >> $log
meatbag sort >> data/sort_gremlin.log 2>&1
echo "[$(date)] sort done: $(wc -l < data/gremlin_sorted.jsonl) sorted" >> $log
meatbag open-corpus >> $log 2>&1
echo "[$(date)] open corpus built; chain finished" >> $log
meatbag report >> $log 2>&1
