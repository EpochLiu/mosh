# Rove Mosh fork

This fork preserves faint/dim text (SGR 2), including the status and hint text
used by Claude Code. It is based on upstream master at
`decd9b705eb81626f694335b8d5940538beb06da`, with Trevor Bernard's upstream
[PR #1404](https://github.com/mobile-shell/mosh/pull/1404) cherry-picked with
its original authorship. Rove changes are maintained on the `rove` branch.

Both endpoints need the fix: the target's `mosh-server` must retain and
serialize faint, and the gateway's `mosh-client` must retain and render it.
The phone uses Rove's web terminal and does not run a Mosh binary. An older
endpoint still ignores SGR 2. No new network message or protocol version is
introduced; this is terminal attribute handling on both sides.

Build and validate on each target platform:

```sh
./autogen.sh
./configure --prefix="$HOME/.local/opt/rove-mosh"
make -j2
make check
make install
```

Select the installation explicitly with Mosh's `--client` and `--server`
options (use an absolute remote server path), or configure the launching
service's PATH. Existing sessions keep using their running binaries; open a
new connection to use the patched pair. Do not terminate tmux or the agent.
Do not assume a binary built on Arch Linux works on Ubuntu: build on each
target or produce a separately validated portable build.

Coverage includes the upstream tmux true-color display comparison, a default
foreground faint/reset display comparison (`emulation-attributes-faint.test`), and a
dedicated `rendition-faint` regression for SGR 2 emission, screen inequality,
bold/faint coexistence, SGR 22/0 resets, and preservation of other attributes
and true color. The upstream test framework uses isolated tmux servers.
