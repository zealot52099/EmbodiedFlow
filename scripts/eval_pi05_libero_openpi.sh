#!/usr/bin/env bash
set -euo pipefail

POLICY_DIR="${POLICY_DIR:-./checkpoints/pi05_libero/pi05_libero_spatial_4090/30000}"
TASK_SUITE="${TASK_SUITE:-libero_spatial}"
POLICY_CONFIG="${POLICY_CONFIG:-pi05_libero}"

echo "Evaluating OpenPI checkpoint with Docker."
echo "POLICY_DIR=${POLICY_DIR}"
echo "TASK_SUITE=${TASK_SUITE}"
echo "POLICY_CONFIG=${POLICY_CONFIG}"

export SERVER_ARGS="--env LIBERO policy:checkpoint --policy.config ${POLICY_CONFIG} --policy.dir ${POLICY_DIR}"
export CLIENT_ARGS="--args.task-suite-name ${TASK_SUITE}"

docker compose -f examples/libero/compose.yml up --build
