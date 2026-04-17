
# Dotfiles symlinked

### Install with stow

```bash
stow .
```

### Manual symlinks

`claude` targets `~/.claude` (not `~/.config/claude`), stow skips it:

```bash
ln -s ./claude ~/.claude
```
