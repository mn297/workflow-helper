# USB controller crash: keep the keyboard

On the Legion 5 laptop, all USB devices share one xHCI controller at PCI address `0000:00:14.0`. The keyboard is one of these devices. If the controller dies, the keyboard dies with it, and only a hard reboot recovers.

## What happened

On 2026-10-23, a RealSense D455 stopped answering at driver start. The kernel log showed this sequence:

1. `uvcvideo 2-5:1.0: Failed to query (GET_DEF) UVC control ...: -110`. The camera did not answer.
2. `usb 2-5: disable of device-initiated U1 failed`. A USB3 link power state failed on the camera.
3. `xHCI host controller not responding, assume dead` and `HC died; cleaning up`. The controller stopped, and every USB device disconnected.

A program probed the stuck camera just before step 3. The probe probably caused the controller to stop.

## The guard

To install the guard, run this command. It asks for the sudo password:

```bash
./ubuntu/setup_usb_guard.sh
```

Then unplug and replug the camera.

The guard has four parts:

| Part | What it does |
|---|---|
| `xhci-watchdog.service` | Reads the kernel log. If a controller dies, it rebinds the controller within about 5 s. The keyboard then comes back without input from you. If the controller dies again within 60 s of a reset, the next reset removes the PCI device and scans the bus again. After 5 resets in a row that do not hold, it logs this and stops resetting. |
| `/usr/local/sbin/xhci-reset` | Rebinds the controller. If the rebind fails, it removes the PCI device and scans the bus again. `--rescan` skips the rebind and does only the remove and scan. It exits with 1 if the driver is not bound at the end. You can run it without a password: `sudo -n /usr/local/sbin/xhci-reset`. |
| `99-usb-guard-power.rules` | Keeps the D455 out of USB autosuspend. |
| `usbcore.quirks=8086:0b5c:k` | Turns off USB3 link power management (U1 and U2) for the D455. The script sets it now and on the kernel command line for each boot. |

To guard more devices, add `vid:pid:k` entries to `QUIRKS` in the script. Also add a matching line to `usb-guard/99-usb-guard-power.rules`.

To remove the guard, run `./ubuntu/setup_usb_guard.sh --remove`. The script then tells you how to remove the boot quirk.

## If a camera hangs

If the camera viewer shows nothing 10 s after start, do these steps:

1. Press Ctrl-C one time.
2. Unplug the camera.
3. Plug the camera in again, and then start the viewer again.

Do not probe a stuck camera with `rs-enumerate-devices` or similar tools. A probe can make the controller stop.

## Checks

```bash
systemctl status xhci-watchdog                      # active (running)
cat /sys/module/usbcore/parameters/quirks           # 8086:0b5c:k
cat /sys/bus/usb/devices/*/power/control            # "on" for the D455
journalctl -t xhci-watchdog -t xhci-reset           # resets that happened
```
