// Answer "where is the mouse?" over D-Bus with the pointer's (x, y) desktop pixels, one reply per call.
//
// This adds no panel item or setting. The position comes from gnome-shell
// itself, so it is right over every window. On Wayland, xdotool asks Xwayland
// instead, which knows the pointer only while it is over an X11 window.
//
//   busctl --user call org.gnome.Shell /org/workflowhelper/Pointer \
//       org.workflowhelper.Pointer GetPosition        # -> ii 2560 800
//
// cursor-brightness.sh matches the point against the xrandr output geometry.
// GNOME finds new extensions only at login, so the first install needs a
// logout. GNOME turns extensions off on the lock screen; the call fails there.

import Gio from 'gi://Gio';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const OBJECT_PATH = '/org/workflowhelper/Pointer';
const INTERFACE_XML = `
<node>
  <interface name="org.workflowhelper.Pointer">
    <method name="GetPosition">
      <arg type="i" name="x" direction="out"/>
      <arg type="i" name="y" direction="out"/>
    </method>
  </interface>
</node>`;

class Pointer {
    GetPosition() {
        const [x, y] = global.get_pointer();
        return [x, y];
    }
}

export default class PointerExtension extends Extension {
    enable() {
        this._dbus = Gio.DBusExportedObject.wrapJSObject(INTERFACE_XML, new Pointer());
        this._dbus.export(Gio.DBus.session, OBJECT_PATH);
    }

    disable() {
        this._dbus.unexport();
        this._dbus = null;
    }
}
