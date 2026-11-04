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

`commandsToSkipShell` must include `toggleSidebarVisibility` (Ctrl+B), `toggleAuxiliaryBar` (Ctrl+Shift+I), and `collapseExplorerFolders` (Ctrl+Shift+Q). If they are missing, the terminal eats those keys.

Also set `vim.handleKeys` `"<C-`>"` and `"<C-b>"` to `false`. Leave `<C-i>` to Vim: it jumps forward, the pair of Ctrl+O. See [`vim_vsc.json`](../../vim_vsc.json).

## Keys

| Key | Action |
|---|---|
| Ctrl+Shift+I | chat panel (toggle; also works in terminal) |
| Ctrl+O / Ctrl+I | Vim jump back / forward (after `gd`) |
| Ctrl+L | chat (focus / add) |
| Ctrl+B | explorer / left sidebar (toggle; also works in terminal) |
| Ctrl+Shift+Q | collapse explorer folders (also works in terminal) |
| Ctrl+Alt+S | agent sidebar (toggle) |
| Ctrl+1 | editor 1 |
| Ctrl+2 | editor 2 |
| Ctrl+3 | terminal (focus) |
| Ctrl+` | terminal (toggle; close returns to the editor that had focus) |

## Allowlist

See [`allowlist.txt`](allowlist.txt).
