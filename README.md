
# Dotfiles symlinked

### New machine setup

```bash
git clone git@github.com:nut-api/dotfiles.git
cd dotfiles
stow .
ln -s ./claude ~/.claude
ln -s ./zsh/.zshenv ~/.zshenv
```

### Install with stow

```bash
stow .
```

### Manual symlinks

`claude` targets `~/.claude` (not `~/.config/claude`), stow skips it:

```bash
ln -s ./claude ~/.claude
```

`zsh/.zshenv` must live at `~/.zshenv` (zsh reads it from `$HOME` before `ZDOTDIR` takes effect, so it can't be stowed normally). It bootstraps `ZDOTDIR=~/.config/zsh`, which is where `zsh/.zshrc` and `zsh/.zprofile` get stowed to:

```bash
ln -s ./zsh/.zshenv ~/.zshenv
```
