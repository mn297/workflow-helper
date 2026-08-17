#!/bin/bash
# Unbind MediaTek mt7925e so S3 resume does not hit pci_pm_resume -110.
# Leaves mt7921e / MT7922 bound. No-ops if 14c3:7925 is not present.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
	exec sudo "$0" "$@"
fi

SRC="$(cd "$(dirname "$0")" && pwd)/mt7925e-unbind"

install -m 755 "$SRC/mt7925e-unbind.sh" /usr/local/sbin/mt7925e-unbind.sh
install -m 644 "$SRC/mt7925e-unbind.service" /etc/systemd/system/mt7925e-unbind.service
install -m 644 "$SRC/80-mt7925e-unbind.rules" /etc/udev/rules.d/80-mt7925e-unbind.rules
install -m 755 "$SRC/mt7925e-unbind.sleep" /lib/systemd/system-sleep/mt7925e-unbind

mkdir -p \
	/etc/systemd/system/systemd-suspend.service.wants \
	/etc/systemd/system/systemd-hibernate.service.wants \
	/etc/systemd/system/systemd-hybrid-sleep.service.wants

ln -sfn /etc/systemd/system/mt7925e-unbind.service \
	/etc/systemd/system/systemd-suspend.service.wants/mt7925e-unbind.service
ln -sfn /etc/systemd/system/mt7925e-unbind.service \
	/etc/systemd/system/systemd-hibernate.service.wants/mt7925e-unbind.service
ln -sfn /etc/systemd/system/mt7925e-unbind.service \
	/etc/systemd/system/systemd-hybrid-sleep.service.wants/mt7925e-unbind.service

systemctl daemon-reload
systemctl enable --now mt7925e-unbind.service
udevadm control --reload

echo "mt7925e unbind installed. Check: lspci -nnk -d 14c3:7925"
echo "MT7922 must stay bound: lspci -nnk -d 14c3:0616"
