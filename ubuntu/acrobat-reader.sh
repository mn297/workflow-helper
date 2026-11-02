#!/usr/bin/env bash
# Install Adobe Acrobat Reader DC into a WineHQ Flatpak prefix, with a launcher and a menu entry.
#
# Newer Reader builds break under Wine, so this pins Reader 2020.013.20074 and
# follows the recipe of the community acrordrdc snap: riched20 + vcrun2015 +
# mspatcha, Windows XP mode, updater and RdrCEF (embedded Chromium) off.
# No sudo: Wine installs as a per-user Flatpak.
#
#   ~/workflow-helper/ubuntu/acrobat-reader.sh              # install; keeps a finished prefix
#   ~/workflow-helper/ubuntu/acrobat-reader.sh --replace    # wipe the prefix and reinstall
#   ~/workflow-helper/ubuntu/acrobat-reader.sh uninstall    # keeps the Wine Flatpak
#   LOGPIXELS=144 ~/workflow-helper/ubuntu/acrobat-reader.sh   # UI scale, 96 = 100 %
#
# Reader 2020 gets no security updates, and its protected mode is off because
# it crashes under Wine. Open only PDFs you trust.
#
# Recipe: https://github.com/mmtrt/acrordrdc-snap
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REF="org.winehq.Wine//stable-26.08"
PREFIX_NAME="${PREFIX_NAME:-acrordr}"
PREFIX="/var/data/$PREFIX_NAME"            # path inside the sandbox
DATA="$HOME/.var/app/org.winehq.Wine/data" # /var/data on the host
HOST_PREFIX="$DATA/$PREFIX_NAME"
CACHE="$DATA/installers"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
SHARE_DIR="${SHARE_DIR:-$HOME/.local/share}"

VERSION="2001320074"
EXE_NAME="AcroRdrDC${VERSION}_en_US.exe"
EXE_URL="https://ardownload2.adobe.com/pub/adobe/reader/win/AcrobatDC/${VERSION}/${EXE_NAME}"
EXE_SHA256="e92dbc7b8ca5dfd6761ca33264beb16f34784f0d944867dd823bcfa8f38e5f40"

PF86="$HOST_PREFIX/drive_c/Program Files (x86)"
READER_DIR="$PF86/Adobe/Acrobat Reader DC/Reader"

REPLACE=0
UNINSTALL=0
for arg in "$@"; do
	case "$arg" in
	--replace) REPLACE=1 ;;
	uninstall) UNINSTALL=1 ;;
	-h | --help)
		echo "usage: $0 [--replace | uninstall]"
		echo "  Adobe Acrobat Reader DC ${VERSION} -> ${HOST_PREFIX}"
		exit 0
		;;
	*)
		echo "usage: $0 [--replace | uninstall]" >&2
		exit 1
		;;
	esac
done

need() { command -v "$1" >/dev/null || { echo "ERROR: missing $1" >&2; exit 1; }; }
need flatpak
need curl
need sha256sum

# Run one command inside the Wine sandbox on this prefix. Each flatpak run has
# a private /tmp, so a wineserver left over from one call is invisible to the
# next, and two wineservers on one prefix break installs. So wait for it to exit.
w() {
	flatpak run --user --env=WINEPREFIX="$PREFIX" --env=WINEDLLOVERRIDES="mscoree,mshtml=" \
		--env=WINEDEBUG=-all --command=sh "$REF" -c '"$@"; rc=$?; wineserver -w; exit $rc' sh "$@"
}

reader_running() {
	local pid
	for pid in $(pgrep -x AcroRd32.exe) $(pgrep -x wineserver); do
		tr '\0' '\n' <"/proc/$pid/environ" 2>/dev/null | grep -qx "WINEPREFIX=$PREFIX" && return 0
	done
	return 1
}

if reader_running; then
	echo "ERROR: Reader or its wineserver runs on ${HOST_PREFIX}. Close Reader first." >&2
	exit 1
fi

if [ "$UNINSTALL" -eq 1 ]; then
	rm -rf "$HOST_PREFIX"
	rm -f "$BIN_DIR/acroread" \
		"$SHARE_DIR/applications/acroread.desktop" \
		"$SHARE_DIR/icons/hicolor/256x256/apps/acroread.png"
	command -v update-desktop-database >/dev/null && update-desktop-database "$SHARE_DIR/applications" || true
	echo "Removed ${HOST_PREFIX}, the launcher and the menu entry."
	echo "Kept the Wine Flatpak and ${CACHE}. To remove them too:"
	echo "  flatpak uninstall --user ${REF}; rm -rf ${CACHE}"
	exit 0
fi

# Pick the Wine UI scale from the primary monitor's DPI. Only HiDPI panels
# scale up: a 1080p 14" laptop at about 157 dpi stays at 100 %.
detect_logpixels() {
	local line px mm dpi
	line=$(xrandr -q 2>/dev/null | grep -E ' connected primary [0-9]+x[0-9]+' | head -1) || true
	[ -n "$line" ] || line=$(xrandr -q 2>/dev/null | grep -E ' connected [0-9]+x[0-9]+' | head -1) || true
	px=$(grep -oE '[0-9]+x[0-9]+\+' <<<"$line" | head -1) || true
	px=${px%%x*}
	mm=$(grep -oE '[0-9]+mm x' <<<"$line" | grep -oE '^[0-9]+') || true
	if ! [[ "$px" =~ ^[0-9]+$ && "$mm" =~ ^[0-9]+$ ]] || [ "$mm" -eq 0 ]; then
		echo 96
		return
	fi
	dpi=$((px * 254 / mm / 10))
	if [ "$dpi" -ge 288 ]; then
		echo 288
	elif [ "$dpi" -ge 192 ]; then
		echo 192
	else
		echo 96
	fi
}
LOGPIXELS="${LOGPIXELS:-$(detect_logpixels)}"
if ! [[ "$LOGPIXELS" =~ ^[0-9]+$ ]] || [ "$LOGPIXELS" -lt 96 ] || [ "$LOGPIXELS" -gt 480 ]; then
	echo "ERROR: LOGPIXELS must be 96..480, got '${LOGPIXELS}'" >&2
	exit 1
fi

echo "== Wine Flatpak ${REF} (per user)"
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
if ! flatpak info --user "$REF" >/dev/null 2>&1; then
	flatpak install --user -y --noninteractive flathub "$REF"
fi

if [ -f "$READER_DIR/AcroRd32.exe" ] && [ "$REPLACE" -ne 1 ]; then
	echo "== Reader already in ${HOST_PREFIX}; pass --replace to reinstall"
else
	if [ -e "$HOST_PREFIX" ]; then
		echo "== Wiping ${HOST_PREFIX}"
		rm -rf "$HOST_PREFIX"
	fi

	echo "== Prefix ${HOST_PREFIX}"
	w wineboot -i
	w winetricks -q riched20 vcrun2015 mspatcha

	echo "== Reader installer"
	mkdir -p "$CACHE"
	if [ -f "$CACHE/$EXE_NAME" ] && ! echo "$EXE_SHA256  $CACHE/$EXE_NAME" | sha256sum -c --quiet 2>/dev/null; then
		echo "cached installer fails its SHA-256; re-downloading"
		rm -f "$CACHE/$EXE_NAME"
	fi
	if [ ! -f "$CACHE/$EXE_NAME" ]; then
		curl -fL --progress-bar -o "$CACHE/$EXE_NAME.part" "$EXE_URL"
		mv "$CACHE/$EXE_NAME.part" "$CACHE/$EXE_NAME"
	fi
	echo "$EXE_SHA256  $CACHE/$EXE_NAME" | sha256sum -c --quiet

	echo "== Silent install"
	rm -rf "$CACHE/dl"
	w 7z -y x "/var/data/installers/$EXE_NAME" -o/var/data/installers/dl >/dev/null
	w sh -c 'cd /var/data/installers/dl && wine setup.exe /sAll /rs /msi EULA_ACCEPT=YES'
	rm -rf "$CACHE/dl"
	if [ ! -f "$READER_DIR/AcroRd32.exe" ]; then
		echo "ERROR: setup.exe finished, but AcroRd32.exe is missing" >&2
		exit 1
	fi

	echo "== Windows XP mode"
	w winetricks -q winxp

	echo "== Updater and RdrCEF off"
	# These exes start at launch and hang or crash under Wine.
	for f in "$PF86/Common Files/Adobe/ARM/1.0/"{armsvc,AdobeARM,AdobeARMHelper}.exe \
		"$READER_DIR/AcroCEF/"{RdrServicesUpdater,RdrCEF}.exe; do
		if [ -e "$f" ]; then mv "$f" "${f}_disabled"; fi
	done
fi

echo "== Registry: updater, cloud services and protected mode off; LogPixels ${LOGPIXELS}"
# Protected mode runs Reader in a Windows sandbox that crashes under Wine.
mkdir -p "$CACHE"
cat >"$CACHE/acrordr-tweaks.reg" <<EOF
Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Adobe\\Acrobat Reader\\DC\\FeatureLockDown]
"bUpdater"=dword:00000000
"bProtectedMode"=dword:00000000

[HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Adobe\\Acrobat Reader\\DC\\FeatureLockDown\\cCloud]
"bAdobeSendPluginToggle"=dword:00000000

[HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Adobe\\Acrobat Reader\\DC\\FeatureLockDown\\cServices]
"bUpdater"=dword:00000000
"bToggleWebConnectors"=dword:00000001
"bTogglePrefsSync"=dword:00000001
"bToggleAdobeDocumentServices"=dword:00000001
"bToggleAdobeSign"=dword:00000001

[HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Adobe\\Acrobat Reader\\DC\\FeatureLockDown\\cSharePoint]
"bDisableSharePointFeatures"=dword:00000001

[HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Adobe\\Acrobat Reader\\DC\\FeatureLockDown\\cWebmailProfiles]
"bDisableWebmail"=dword:00000001

[HKEY_LOCAL_MACHINE\\SOFTWARE\\Adobe\\Adobe ARM\\Legacy\\Reader\\{AC76BA86-7AD7-1033-7B44-AC0F074E4100}]
"Mode"=dword:00000000

[HKEY_CURRENT_USER\\Software\\Adobe\\Acrobat Reader\\DC\\Privileged]
"bProtectedMode"=dword:00000000

[HKEY_CURRENT_USER\\Control Panel\\Desktop]
"LogPixels"=dword:$(printf '%08x' "$LOGPIXELS")
EOF
# Reader is 32-bit, so import with both regedits to land in both registry views.
w wine 'C:\windows\regedit.exe' /S /var/data/installers/acrordr-tweaks.reg
w wine 'C:\windows\syswow64\regedit.exe' /S /var/data/installers/acrordr-tweaks.reg

echo "== Launcher ${BIN_DIR}/acroread"
install -D -m 755 "$HERE/acrobat-reader/acroread" "$BIN_DIR/acroread"

echo "== Menu entry and icon"
icon="$SHARE_DIR/icons/hicolor/256x256/apps/acroread.png"
if command -v convert >/dev/null; then
	rm -rf "$CACHE/icon"
	w 7z e -y "$PREFIX/drive_c/Program Files (x86)/Adobe/Acrobat Reader DC/Reader/AcroRd32.exe" \
		'.rsrc/1033/ICON/1.ico' -o/var/data/installers/icon >/dev/null
	mkdir -p "$(dirname "$icon")"
	convert "$CACHE/icon/1.ico[0]" -resize 256x256 "$icon"
	rm -rf "$CACHE/icon"
else
	echo "warning: ImageMagick convert missing; the menu entry gets no icon"
fi

mkdir -p "$SHARE_DIR/applications"
cat >"$SHARE_DIR/applications/acroread.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Adobe Acrobat Reader DC
GenericName=PDF Reader
Comment=View, fill and sign PDF files (runs under Wine)
Exec=env ACROREAD_PREFIX=${PREFIX} ${BIN_DIR}/acroread %f
Icon=acroread
Terminal=false
Categories=Office;Viewer;
MimeType=application/pdf;
StartupWMClass=acrord32.exe
EOF
command -v update-desktop-database >/dev/null && update-desktop-database "$SHARE_DIR/applications" || true

echo
echo "Installed Reader $(strings -el "$READER_DIR/AcroRd32.exe" 2>/dev/null | grep -A1 -m1 ProductVersion | tail -1) in ${HOST_PREFIX}"
echo "Open:     acroread file.pdf   (or the 'Adobe Acrobat Reader DC' menu entry)"
echo "Default:  xdg-mime default acroread.desktop application/pdf"
