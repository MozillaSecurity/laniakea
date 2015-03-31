# Target desscription for Firefox
TARGET_PRODUCT="mozilla-inbound-linux64-asan"
TARGET_LOCATION="ftp.mozilla.org/pub/mozilla.org/firefox/tinderbox-builds/${TARGET_PRODUCT}/latest"
TARGET_URL="ftp://${TARGET_LOCATION}"
retry wget --force-directories --no-parent --glob=on ${TARGET_URL}/firefox-*.en-US.linux-x86_64-asan.tar.bz2
retry wget --force-directories --no-parent --glob=on -O ${TARGET_LOCATION}/changeset.json ${TARGET_URL}/firefox-*-asan.json
tar xvfj ${TARGET_LOCATION}/firefox-*.en-US.linux-x86_64-asan.tar.bz2
TARGET_VERSION=`cat ${TARGET_LOCATION}/firefox-*.json | python -c 'import sys,json; print(json.load(sys.stdin)["moz_source_stamp"])'`
