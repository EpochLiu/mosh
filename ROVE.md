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

## Gateway installation without restarting Rove

Install the gateway's native binaries in `~/.local/opt/rove-mosh/bin/` and
install `scripts/rove-launcher.py` there as the executable `mosh`. Create
`~/.local/opt/rove-mosh/hosts.json` containing exact target arguments, for
example `["alice@example.test"]`. Symlink the gateway's `/usr/local/bin/mosh`
to this launcher, and `/usr/local/bin/mosh-client` to the installed client.
The Rove service must have `/usr/local/bin` before `/usr/bin` in its PATH.
The distro's `/usr/bin/mosh` and packaged binaries remain intact.

Install each target platform's server in that remote user's
`~/.local/opt/rove-mosh/bin/mosh-server`. The launcher selects this path only
for hosts in `hosts.json`. Other hosts retain the default remote server;
explicit command-line `--client` and `--server` options take precedence.
Remote installation does not require sudo. Replace binaries with a temporary
file and atomic rename, rather than overwriting a running executable.

Run `python3 scripts/rove-launcher-test.py` to verify host selection and
explicit overrides. Confirm the installed binary's `--version`, shared
library resolution, and actual dim/normal attributes over each live UDP route.
For example, run the following from a gateway with Rove's node dependencies:

```sh
python3 scripts/rove-live-smoke.py --host alice@example.test \
  --udp-ports 60000:60010 --ssh-port 22 \
  --xterm-module /path/to/rove/node_modules/@xterm/headless
```

The smoke test starts a temporary Python process through Mosh, verifies dim
and normal cells with xterm, and quits the Mosh connection cleanly. It does
not attach to an existing tmux session.

No gateway restart is required. Existing Rove connections retain their running
Mosh processes, even after a browser refresh. Close the old connection in Rove
and select the same tmux session again to load both new binaries. Do not kill
the tmux session or its Claude process.
