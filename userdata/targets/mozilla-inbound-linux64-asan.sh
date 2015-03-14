# Target desscription for Firefox
TARGET_PRODUCT="mozilla-inbound-linux64-asan"
TARGET_LOCATION="ftp.mozilla.org/pub/mozilla.org/firefox/tinderbox-builds/${TARGET_PRODUCT}/latest"
TARGET_URL="ftp://${TARGET_LOCATION}"
retry wget --force-directories --no-parent --glob=on ${TARGET_URL}/firefox-*.en-US.linux-x86_64-asan.tar.bz2
retry wget --force-directories --no-parent --glob=on ${TARGET_URL}/*.txt -O ${TARGET_LOCATION}/revision.txt
tar xvfj ${TARGET_LOCATION}/firefox-*.en-US.linux-x86_64-asan.tar.bz2
TARGET_VERSION=`cat ${TARGET_LOCATION}/revision.txt`
