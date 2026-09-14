# Mac

## Cursor keys

Restore from [`cursor/keybindings.json`](cursor/keybindings.json):

```bash
mkdir -p ~/Library/Application\ Support/Cursor/User
cp ~/workflow-helper/mac/cursor/keybindings.json ~/Library/Application\ Support/Cursor/User/keybindings.json
```

See [`cursor/README.md`](cursor/README.md) for the full map. `./setup.sh` copies the same file after installing Cursor.

## zsh syntax highlighting

Command colors as you type. Plugin lives in `~/.zsh/zsh-syntax-highlighting` (must be sourced last in `.zshrc`).

```bash
mkdir -p ~/.zsh
git clone --depth 1 https://github.com/zsh-users/zsh-syntax-highlighting.git ~/.zsh/zsh-syntax-highlighting
```

Add this last line to `~/.zshrc` (already in [`.zshrc`](.zshrc)):

```bash
source ~/.zsh/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
```

## Finder: Open with Cursor (⌃⌘P)

Select a folder (or file) in Finder and press Control-Command-P.

```bash
cp -R ~/workflow-helper/mac/Open\ with\ Cursor.workflow ~/Library/Services/
defaults write pbs NSServicesStatus -dict-add \
  "(null) - Open with Cursor - runWorkflowAsService" \
  '{ enabled_context_menu = 1; enabled_services_menu = 1; "key_equivalent" = "@^p"; }'
defaults write com.apple.finder NSUserKeyEquivalents -dict-add "Open with Cursor" "@^p"
/System/Library/CoreServices/pbs -flush
/System/Library/CoreServices/pbs -update
```

Also available from **Finder → Services → Open with Cursor**. First use may ask to control Finder; click OK. If the shortcut does not fire, make Finder frontmost, or log out and back in.

## Finder: Open in Terminal (⌃⌘T)

Click a Finder window (selected item or just the open folder) and press Control-Command-T. First use may ask to control Finder; click OK. Finder must be frontmost.

```bash
cp -R ~/workflow-helper/mac/Open\ in\ Terminal.workflow ~/Library/Services/
defaults write pbs NSServicesStatus -dict-add \
  "(null) - Open in Terminal - runWorkflowAsService" \
  '{ enabled_context_menu = 1; enabled_services_menu = 1; "key_equivalent" = "@^t"; }'
defaults write com.apple.finder NSUserKeyEquivalents -dict-add "Open in Terminal" "@^t"
/System/Library/CoreServices/pbs -flush
/System/Library/CoreServices/pbs -update
```

VS Code equivalent (no shortcut bound): [`Open in Visual Studio Code.workflow`](Open%20in%20Visual%20Studio%20Code.workflow).
