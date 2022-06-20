#!/bin/sh

# This script will create udevrule which will automatically give read/write permisison and run the keebie.service as soon as you plug your keyboard
# find the values vendor-id and product-id by using lsusb command
# Note make sure you copy keebie.service to /etc/systemd/system before executing this script as sudo

# Usage example:
: '
# 1. find vendor/product id
lsusb 
# 2. make script executable
chmod +x ./udevRule.sh
# 3. generate udev rule file, replace 0c45 and 5004 with your vendor/product id
sudo ./udevRule.sh 'ATTRS{idVendor}=="04d9", ATTRS{idProduct}=="0326"' 85-keebie-systemd.rules
'

touch /etc/udev/rules.d/"$2"
cd /etc/udev/rules.d/

echo 'SUBSYSTEM=="input", '"$1"'MODE="0666", ENV{SYSTEMD_WANTS}="keebie.service"  TAG+="systemd"' > "$2"

sleep 1s

# No need to restart the system
udevadm control --reload-rules 
