#!/usr/bin/env python3
"""Check dim and normal cells over a real, isolated Rove Mosh connection.

Requires node and @xterm/headless (already bundled with the Rove gateway).
Does not attach to or modify any existing tmux session.
"""

import argparse
import errno
import fcntl
import json
import os
import pty
import select
import signal
import struct
import subprocess
import termios
import time
import uuid

CHECK = r"""
const {Terminal} = require(process.argv[1]);
const terminal = new Terminal({cols:110, rows:32, allowProposedApi:true});
const data = require('fs').readFileSync(0);
terminal.write(data, () => {
  try {
    const result = {};
    for (const [marker, expected] of [[process.argv[2], true], [process.argv[3], false]]) {
      let found = false;
      const buffer = terminal.buffer.active;
      for (let y=0; y<buffer.length; y++) {
        const row=buffer.getLine(y), x=row.translateToString().indexOf(marker);
        if (x<0) continue;
        for (let n=0; n<marker.length; n++) {
          if (!!row.getCell(x+n).isDim() !== expected) throw Error('Wrong dim attribute: '+marker);
        }
        found=true;
      }
      if (!found) throw Error('Missing marker: '+marker);
      result[expected ? 'dim' : 'normal']=true;
    }
    console.log(JSON.stringify(result));
  } catch (error) {
    console.error(error.message);
    process.exitCode=1;
  } finally {terminal.dispose();}
});
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--ssh-port", type=int, default=22)
    parser.add_argument("--udp-ports", required=True)
    parser.add_argument("--mosh", default="mosh")
    parser.add_argument("--xterm-module", default="@xterm/headless")
    parser.add_argument("--capture-output", help="Optional private file for this isolated test's terminal bytes")
    args = parser.parse_args()
    token = uuid.uuid4().hex[:12]
    dim, normal = "ROVE_DIM_" + token, "ROVE_NORMAL_" + token
    payload = ("import time,sys; "
               "sys.stdout.write('\\x1b[2J\\x1b[H\\x1b[2m" + dim +
               "\\x1b[22m " + normal + "\\r\\n'); sys.stdout.flush(); time.sleep(40)")
    command = [args.mosh, "--predict=never",
               "--ssh=ssh -p " + str(args.ssh_port) +
               " -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8",
               "-p", args.udp_ports, args.host, "--", "python3", "-u", "-c", payload]
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 32, 110, 0, 0))

    def setup():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)

    process = None
    output = bytearray()
    result = None
    try:
        process = subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave,
                                   env={**os.environ, "TERM": "xterm-256color", "LANG": "C.UTF-8",
                                        "MOSH_ESCAPE_KEY": "\x1e"}, preexec_fn=setup)
        os.close(slave)
        slave = None
        deadline = time.monotonic() + 30
        seen = None
        while time.monotonic() < deadline:
            if select.select([master], [], [], .2)[0]:
                try:
                    data = os.read(master, 65536)
                except OSError as error:
                    if error.errno == errno.EIO:
                        break
                    raise
                if not data:
                    break
                output.extend(data)
            if normal.encode() in output and seen is None:
                seen = time.monotonic()
            if seen is not None and time.monotonic() - seen > .5:
                break
        if args.capture_output:
            fd = os.open(args.capture_output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as file:
                file.write(output)
        checked = subprocess.run(["node", "-e", CHECK, args.xterm_module, dim, normal],
                                 input=bytes(output), capture_output=True, timeout=10)
        if checked.returncode:
            raise RuntimeError(checked.stderr.decode(errors="replace").strip())
        result = {"host": args.host, **json.loads(checked.stdout)}
    finally:
        if slave is not None:
            os.close(slave)
        if process is not None and process.poll() is None:
            os.write(master, b"\x1e.")
            try:
                process.wait(timeout=6)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=5)
        os.close(master)
    if process.returncode != 0:
        raise RuntimeError("Mosh did not close cleanly: " + str(process.returncode))
    print(json.dumps({**result, "closed_cleanly": True}))


if __name__ == "__main__":
    main()
