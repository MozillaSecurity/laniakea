# Create binary FuzzManager configuration
cat > /home/ubuntu/firefox/firefox.fuzzmanagerconf << EOL
[Main]
platform = x86-64
product = ${TARGET_PRODUCT}
product_version = ${TARGET_VERSION}
os = `uname -s`
EOL
