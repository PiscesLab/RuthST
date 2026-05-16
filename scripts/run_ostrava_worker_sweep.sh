#!/bin/bash
set -e

cd /users/jliu312/RuthST
export PYTHONPATH=$PWD:$PYTHONPATH

mkdir -p logs logs/collectl

PORTION=0pc
WORKERS_LIST="1 2 4 8 16"
REPEATS=3

for w in $WORKERS_LIST
do
  for r in $(seq 1 $REPEATS)
  do
    RUN_ID=ostrava_${PORTION}_w${w}_r${r}
    LOG_FILE=logs/${RUN_ID}.log
    COLLECTL_PREFIX=logs/collectl/${RUN_ID}

    echo "========================================"
    echo "[Run] $RUN_ID"
    echo "[Log] $LOG_FILE"
    echo "[Collectl] ${COLLECTL_PREFIX}"
    echo "========================================"

    echo "[Clean] stop old Parsl workers"
    bash scripts/stop_parssl.sh || true

    echo "[Clean] remove old outputs"
    rm -rf data/processed/*
    rm -rf data/ruth/*

    echo "[Monitor] start collectl"
    collectl -scmd -i 1 -f ${COLLECTL_PREFIX} >/dev/null 2>&1 &
    COLLECTL_PID=$!

    echo "[Experiment] start"
    /usr/bin/time -v python scripts/run_conversion_eval.py \
      --portion $PORTION \
      --workers $w \
      > $LOG_FILE 2>&1

    echo "[Monitor] stop collectl"
    kill $COLLECTL_PID || true
    sleep 2

    echo "[Clean] stop Parsl workers after run"
    bash scripts/stop_parssl.sh || true

    echo "[Done] $RUN_ID"
  done
done
