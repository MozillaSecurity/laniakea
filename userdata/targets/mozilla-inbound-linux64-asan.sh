# Download ASan build of Firefox
ARTIFACT_NAME="en-US.linux-x86_64-asan.tar.bz2"
TASK_ID=$(wget -q -O - https://index.taskcluster.net/v1/task/gecko.v2.mozilla-inbound.latest.firefox.linux64-asan | python3 -c "import json,sys; print(json.load(sys.stdin)['taskId'])")
ARTIFACT_URL=$(wget -q -O - https://queue.taskcluster.net/v1/task/$TASK_ID/artifacts | python3 -c "import json,sys; [print(build['name']) for build in json.load(sys.stdin)['artifacts'] if (build['name'].endswith('$ARTIFACT_NAME'))]")
wget -O - "https://queue.taskcluster.net/v1/task/$TASK_ID/artifacts/$ARTIFACT_URL" | tar xvja

# Download build information of Firefox
CHANGESET_JSON="en-US.linux-x86_64-asan.json"
CHANGESET_URL=$(wget -q -O - https://queue.taskcluster.net/v1/task/$TASK_ID/artifacts | python3 -c "import json,sys; [print(build['name']) for build in json.load(sys.stdin)['artifacts'] if (build['name'].endswith('$CHANGESET_JSON'))]")
CHANGESET=$(wget -q -O - "https://queue.taskcluster.net/v1/task/$TASK_ID/artifacts/$CHANGESET_URL" | python -c "import sys,json; print(json.load(sys.stdin)['moz_source_stamp'])")
