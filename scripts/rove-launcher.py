#!/usr/bin/python3
"""Select the Rove client and opt-in servers without replacing distro files.

Install as PREFIX/bin/mosh and symlink it from a directory on the gateway's
PATH. PREFIX/hosts.json is a JSON list of exact [user@]host arguments whose
servers are installed at ~/.local/opt/rove-mosh/bin/mosh-server. Other hosts
keep using their default server. Explicit CLI --client/--server options win.
"""

import json
import os
from pathlib import Path
import sys


def command(prefix, args):
    targets = json.loads((prefix / "hosts.json").read_text())
    if not isinstance(targets, list) or any(not isinstance(t, str) for t in targets):
        raise ValueError("hosts.json must contain a list of host arguments")
    options = ["--client=" + str(prefix / "bin/mosh-client")]
    # Mosh passes --server as a remote shell command, so the target's shell
    # expands this tilde. It refers to the authenticated remote user's home.
    # Parse only launcher arguments, never the remote command after the host.
    host = None
    value_options = {"--ssh", "--client", "--server", "--predict", "--port", "--bind-server", "--family", "-p"}
    skip = False
    for i, arg in enumerate(args):
        if skip:
            skip = False
            continue
        if arg == "--":
            host = args[i + 1] if i + 1 < len(args) else None
            break
        if arg in value_options:
            skip = True
        elif not arg.startswith("-"):
            host = arg
            break
    if host in targets:
        options.append("--server=~/.local/opt/rove-mosh/bin/mosh-server")
    return ["/usr/bin/mosh", *options, *args]


if __name__ == "__main__":
    prefix = Path(__file__).resolve().parent.parent
    argv = command(prefix, sys.argv[1:])
    os.execv(argv[0], argv)
