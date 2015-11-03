# Target desscription for Firefox
TARGET_PRODUCT="mozilla-inbound-linux64-asan"
TARGET_LOCATION="ftp.mozilla.org/pub/firefox/tinderbox-builds/${TARGET_PRODUCT}/latest/"
TARGET_URL="https://${TARGET_LOCATION}"
retry wget -r -l1 -np -A "firefox-*.en-US.linux-x86_64-asan.tar.bz2" "${TARGET_URL}"
retry wget -r -l1 -np -A "firefox-*-asan.json" "${TARGET_URL}"
tar xvfj ${TARGET_LOCATION}/firefox-*.en-US.linux-x86_64-asan.tar.bz2
TARGET_VERSION=`cat ${TARGET_LOCATION}/firefox-*.json | python -c 'import sys,json; print(json.load(sys.stdin)["moz_source_stamp"])'`
