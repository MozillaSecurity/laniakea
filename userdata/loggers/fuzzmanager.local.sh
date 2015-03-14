# Create base FuzzManager configuration
cat > /home/ubuntu/.fuzzmanagerconf << EOL
[Main]
serverhost = darpa.spdns.de
serverport = 8000
serverproto = http
serverauthtoken = 8fcaa1c5937490bb3fc6c25598e91bb86855efb4
sigdir = /home/ubuntu/signatures
EOL
echo "clientid =" `curl --retry 5 -s http://169.254.169.254/latest/meta-data/public-hostname` >> /home/ubuntu/.fuzzmanagerconf

# Create binary FuzzManager configuration
cat > /home/ubuntu/firefox/firefox.fuzzmanagerconf << EOL
[Main]
platform = x86-64
product = ${TARGET_PRODUCT}
product_version = ${TARGET_VERSION}
os = `uname -s`
EOL
