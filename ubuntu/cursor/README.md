# Cursor (Linux)

## Restore

```bash
mkdir -p ~/.config/Cursor/User
cp ~/workflow-helper/ubuntu/cursor/keybindings.json ~/.config/Cursor/User/keybindings.json
```

Merge [`settings.json`](settings.json) into `~/.config/Cursor/User/settings.json`.

Install extensions from [`extensions.txt`](extensions.txt):

```bash
grep -v '^#' ~/workflow-helper/ubuntu/cursor/extensions.txt | while read -r ext; do
  cursor --install-extension "$ext"
done
```

`commandsToSkipShell` must include `toggleSidebarVisibility` (Ctrl+B) and `toggleAuxiliaryBar` (Ctrl+I). If they are missing, the terminal eats both keys. Ctrl+I is ASCII Tab.

Also set `vim.handleKeys` `"<C-i>"`, `"<C-`>"`, `"<C-b>"` to `false`. See [`vim_vsc.json`](../../vim_vsc.json).

## Keys

| Key | Action |
|---|---|
| Ctrl+I | chat panel (toggle; also works in terminal) |
| Ctrl+L | chat (focus / add) |
| Ctrl+B | explorer / left sidebar (toggle; also works in terminal) |
| Ctrl+Alt+S | agent sidebar (toggle) |
| Ctrl+1 | editor 1 |
| Ctrl+2 | editor 2 |
| Ctrl+3 | terminal (focus) |
| Ctrl+` | terminal (toggle) |

## Allowlist

See [`allowlist.txt`](allowlist.txt).
