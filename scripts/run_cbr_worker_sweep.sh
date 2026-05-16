#!/bin/bash
set -e

cd /users/jliu312/RuthST
export PYTHONPATH=$PWD:$PYTHONPATH

mkdir -p logs logs/collectl results/cbr_worker_sweep

CITY=cbr
PORTION=2pc
CHUNK_SIZE=16000000
WORKERS_LIST="4 8 16 32 2 1"

for w in $WORKERS_LIST
do
  RUN_ID=${CITY}_${PORTION}_w${w}_chunk${CHUNK_SIZE}
  LOG_FILE=logs/${RUN_ID}.log
  COLLECTL_PREFIX=logs/collectl/${RUN_ID}

  echo "========================================"
  echo "[Run] $RUN_ID"
  echo "[Log] $LOG_FILE"
  echo "[Collectl] $COLLECTL_PREFIX"
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
    --city $CITY \
    --portion $PORTION \
    --workers $w \
    --chunk-size $CHUNK_SIZE \
    --skip-adj \
    > $LOG_FILE 2>&1

  echo "[Monitor] stop collectl"
  kill $COLLECTL_PID || true
  sleep 2

  echo "[Clean] stop Parsl workers after run"
  bash scripts/stop_parssl.sh || true

  echo "[Done] $RUN_ID"
done
