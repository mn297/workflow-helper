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

## LaTeX

Full TeX Live (no TeXShop), about 5 GB. Packages are already included. `latexmk` builds with `pdflatex`. Aux files go in `build/` so OneDrive does not sync them. PDF is `build/<name>.pdf`. Quit Cursor fully and reopen it after the install so it sees `/Library/TeX/texbin`.

```bash
brew install --cask mactex-no-gui

grep -q '/Library/TeX/texbin' ~/.zshrc || echo 'export PATH="/Library/TeX/texbin:$PATH"' >> ~/.zshrc
export PATH="/Library/TeX/texbin:$PATH"
hash -r

which pdflatex latexmk
pdflatex --version | head -1

cursor --install-extension James-Yu.latex-workshop
```

From the directory that contains the `.tex` file (for ME 641 notes, `notes/`):

```bash
cp ~/workflow-helper/mac/latex/.latexmkrc .latexmkrc
mkdir -p .vscode
cp ~/workflow-helper/mac/latex/settings.json .vscode/settings.json

latexmk -pdf parametric_models_summary.tex
open build/parametric_models_summary.pdf
```

Saving the `.tex` file in Cursor rebuilds the PDF in an editor tab. Only if a later package is missing:

```bash
sudo tlmgr update --self
sudo tlmgr install packagename
```
