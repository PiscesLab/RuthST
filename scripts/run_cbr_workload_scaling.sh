#!/bin/bash
set -e

cd /users/jliu312/RuthST
export PYTHONPATH=$PWD:$PYTHONPATH

#mkdir -p logs logs/collectl results/cbr_workload_scaling

CITY=cbr
WORKERS=16
CHUNK_SIZE=16000000
#PORTIONS="7pc 6pc 4pc 2pc 1pc"
PORTIONS="2pc 1pc"

for portion in $PORTIONS
do
  RUN_ID=${CITY}_${portion}_w${WORKERS}_chunk${CHUNK_SIZE}
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
    --portion $portion \
    --workers $WORKERS \
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
