// Tell cursor-brightness.sh which monitor the mouse cursor is on, by connector name.
//
// Wayland gives other programs no global cursor position, so the script asks
// the shell:
//
//   $ busctl --user call org.gnome.Shell /org/workflowhelper/CursorBrightness \
//         org.workflowhelper.CursorBrightness GetConnector
//   s "DP-1"
//
// The name is Mutter's connector name, which is the kernel's DRM name except
// HDMI-A-1 shows as HDMI-1. The script reads the EDID from /sys/class/drm.
//
// Mutter's own GetCurrentState gives the connector of each logical monitor.
// The monitor under the cursor is the one whose top-left corner matches.
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const OBJECT_PATH = '/org/workflowhelper/CursorBrightness';
const IFACE = `
<node>
  <interface name="org.workflowhelper.CursorBrightness">
    <method name="GetConnector">
      <arg type="s" name="connector" direction="out"/>
    </method>
  </interface>
</node>`;

class Service {
    GetConnectorAsync(_params, invocation) {
        const {x, y} = global.display.get_monitor_geometry(
            global.display.get_current_monitor());
        Gio.DBus.session.call(
            'org.gnome.Mutter.DisplayConfig', '/org/gnome/Mutter/DisplayConfig',
            'org.gnome.Mutter.DisplayConfig', 'GetCurrentState',
            null, null, Gio.DBusCallFlags.NONE, -1, null,
            (bus, res) => {
                try {
                    const [, , logical] = bus.call_finish(res).deepUnpack();
                    // (x, y, scale, transform, primary, [(connector, ...)], props)
                    const hit = logical.find(([lx, ly]) => lx === x && ly === y);
                    if (!hit)
                        throw new Error(`no logical monitor at ${x},${y}`);
                    invocation.return_value(new GLib.Variant('(s)', [hit[5][0][0]]));
                } catch (e) {
                    invocation.return_error_literal(
                        Gio.DBusError, Gio.DBusError.FAILED, e.message);
                }
            });
    }
}

export default class CursorBrightnessExtension extends Extension {
    enable() {
        this._dbus = Gio.DBusExportedObject.wrapJSObject(IFACE, new Service());
        this._dbus.export(Gio.DBus.session, OBJECT_PATH);
    }

    disable() {
        this._dbus.unexport();
        this._dbus = null;
    }
}
