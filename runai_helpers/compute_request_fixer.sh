#!/bin/bash

### purpose: fix all compute assets with 0M or 0G in the memory request.

### usage:
# export RUNAI_CTRL_PLANE_URL="..."
# export RUNAI_TOKEN="..."
# bash compute_request_fixer.sh

output_folder="runai_computes_$(date +%d-%m-%Y_%H-%M-%S)"
mkdir $output_folder
cd $output_folder
pwd

runai_ctrl_plane_url=$(printenv RUNAI_CTRL_PLANE_URL)
token=$(printenv RUNAI_TOKEN)

computes_all_json_file="computes_all.json"
computes_noreq_json_file="computes_noreq.json"

echo $runai_ctrl_plane_url
echo $token | wc

get_all_computes() {
  curl -s "$runai_ctrl_plane_url/api/v1/asset/compute?usageInfo=true" \
    -H 'accept: application/json, text/plain, */*' \
    -H 'accept-language: en-US,en;q=0.9' \
    -H "authorization: Bearer $token" | jq > "$computes_all_json_file"

    jq -r '.entries[] | select(.spec.cpuMemoryRequest == "0M" or .spec.cpuMemoryRequest == "0G") | .meta.id' "$computes_all_json_file" > $computes_noreq_json_file

    echo "compute files length:"
    cat $computes_all_json_file | wc
    cat $computes_noreq_json_file | wc
}

get_and_modify_compute() {
  local compute_uuid="$1"

  if [[ -z "$token" || -z "$compute_uuid" ]]; then
    echo "Error: Both token and compute_uuid are required." >&2
    return 1
  fi

  local modified_file="${compute_uuid}_modified.json"
  local original_file="${compute_uuid}_original.json"

  curl -s "$runai_ctrl_plane_url/api/v1/asset/compute/$compute_uuid" \
    -H 'accept: application/json, text/plain, */*' \
    -H 'accept-language: en-US,en;q=0.9' \
    -H "authorization: Bearer $token" \
    -H 'content-type: application/json' | jq > "$original_file"

  cat $original_file | jq '.meta |= {name: .name} | .spec.cpuMemoryRequest = "1M"' > "$modified_file"

  curl "$runai_ctrl_plane_url/api/v1/asset/compute/$compute_uuid" \
    -X 'PUT' \
    -H 'accept: application/json, text/plain, */*' \
    -H 'accept-language: en-US,en;q=0.9' \
    -H "authorization: Bearer $token" \
    -H 'content-type: application/json' \
    --data-binary "@$modified_file"

  if [[ $? -ne 0 ]]; then
    echo "Error: Command failed (curl or jq)." >&2
    return 1
  fi

  echo "Successfully fetched and modified compute $compute_uuid."
  echo

  return 0
}

get_all_computes

while IFS= read -r compute_uuid; do
  if [[ -z "$compute_uuid" ]] || [[ "$compute_uuid" == \#* ]]; then
    continue
  fi

  echo "Processing compute UUID: $compute_uuid"
  get_and_modify_compute "$compute_uuid"

  if [[ $? -ne 0 ]]; then
    echo "Error processing compute UUID: $compute_uuid" >&2
  fi
done < "$computes_noreq_json_file"

echo "Finished processing all compute UUIDs."
cd ..
pwd