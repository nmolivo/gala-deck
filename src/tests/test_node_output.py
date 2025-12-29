import time
import subprocess
import sys

proc = subprocess.Popen(
    ["node", "vapi-doc-coding-mcp/build/index.js"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=0
)

# Send initialize request (JSON-RPC format)
init_msg = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n'

print("Sending:", init_msg.strip())
proc.stdin.write(init_msg)
proc.stdin.flush()

# Read response (wait 2 seconds)
time.sleep(2)

# Check what came back
stdout_data = proc.stdout.read()
stderr_data = proc.stderr.read()

print("\n=== STDOUT ===")
print(repr(stdout_data))
print("\n=== STDERR ===")
print(repr(stderr_data))

proc.kill()
