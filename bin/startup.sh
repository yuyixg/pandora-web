#!/bin/bash

PANDORA_ARGS=""
PANDORA_COMMAND="pandora"
USER_CONFIG_DIR="/data"

# Set email, password, and mfa from environment variables if they are set
if [ -n "${OPENAI_EMAIL}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --email ${OPENAI_EMAIL}"
fi

if [ -n "${OPENAI_PASSWORD}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --password ${OPENAI_PASSWORD}"
fi

if [ -n "${OPENAI_MFA_CODE}" ]; then
  PANDORA_ARGS="${OPENAI_MFA_CODE} --mfa ${OPENAI_MFA_CODE}"
fi

if [ -n "${OPENAI_API_PREFIX}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --proxy_api ${OPENAI_API_PREFIX}"
fi

if [ -n "${OPENAI_LOGIN_URL}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --login_url ${OPENAI_LOGIN_URL}"
fi

if [ -n "${PANDORA_PROXY}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} -p ${PANDORA_PROXY}"
fi

# Handle access token and tokens file
if [ -n "${PANDORA_ACCESS_TOKEN}" ]; then
  mkdir -p "${USER_CONFIG_DIR}"
  echo "${PANDORA_ACCESS_TOKEN}" >"${USER_CONFIG_DIR}/access_token.dat"
fi

if [ -n "${PANDORA_TOKENS_FILE}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --tokens_file ${PANDORA_TOKENS_FILE}"
fi

# Server mode
if [ -n "${PANDORA_SERVER}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} -s ${PANDORA_SERVER}"
  if [ -n "${PANDORA_SITE_PASSWORD}" ]; then
    PANDORA_ARGS="${PANDORA_ARGS} --site_password ${PANDORA_SITE_PASSWORD}"
  fi
fi

# Model selection
if [ -n "${PANDORA_GPT4_MODEL}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --gpt4 ${PANDORA_GPT4_MODEL}"
fi

if [ -n "${PANDORA_GPT35_MODEL}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --gpt35 ${PANDORA_GPT4_MODEL}"
fi

# History settings
if [ -n "${PANDORA_HISTORY_COUNT}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --history_count ${PANDORA_HISTORY_COUNT}"
fi

if [ -n "${PANDORA_BEST_HISTORY}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --best_history"
fi

# Other options
if [ -n "${PANDORA_TRUE_DELETE}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --true_del"
fi

if [ -n "${PANDORA_LOCAL_OPTION}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} -l"
fi

if [ -n "${PANDORA_TIMEOUT}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --timeout ${PANDORA_TIMEOUT}"
fi

if [ -n "${PANDORA_OAI_ONLY}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --oai_only"
fi

if [ -n "${PANDORA_OLD_LOGIN}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --old_login"
fi

if [ -n "${PANDORA_OLD_CHAT}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --old_chat"
fi

if [ -n "${PANDORA_API}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} -a"
fi

if [ -n "${PANDORA_LOGIN_LOCAL}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} -login_local"
fi

if [ -n "${PANDORA_VERBOSE}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} -v"
fi

if [ -n "${PANDORA_THREADS}" ]; then
  PANDORA_ARGS="${PANDORA_ARGS} --threads ${PANDORA_THREADS}"
fi

if [ -n "${PANDORA_CLOUD}" ]; then
  PANDORA_COMMAND="pandora-cloud"
fi

export USER_CONFIG_DIR

# Execute the Pandora command with the arguments
# shellcheck disable=SC2086
$(command -v ${PANDORA_COMMAND}) ${PANDORA_ARGS}
