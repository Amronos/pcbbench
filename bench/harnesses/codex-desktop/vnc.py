# /// script
# dependencies = ["asyncvnc", "numpy", "pillow"]
# ///
"""Drive the Mac's Screen Sharing over the SSH tunnel on localhost:15900.

    uv run vnc.py shot out.png
    uv run vnc.py click 120 380 [shot out.png]
    uv run vnc.py key Super_L+space type 'hello' key Return shot out.png

Actions run in order on one connection. vncdotool connects but its input is
ignored by macOS 26 Screen Sharing; asyncvnc's input works.
"""

import asyncio
import os
import sys

import asyncvnc
from PIL import Image

PASSWORD_FILE = os.path.expanduser("~/.config/pcbbench/mac-ec2-user-password")
PORT = int(os.environ.get("MAC_VNC_PORT", "15900"))


async def run(args: list[str]) -> None:
	password = open(PASSWORD_FILE).read().strip()
	async with asyncvnc.connect("localhost", PORT, username="ec2-user", password=password) as client:
		# Screen Sharing drops input for about the first second of a session. Screenshots alone
		# skip this, so they don't move the mouse under a running agent.
		if not all(arg == "shot" or arg.endswith(".png") for arg in args):
			for i in range(6):
				client.mouse.move(1 + i, 1)
				await asyncio.sleep(0.5)
		while args:
			action, *args = args
			if action == "shot":
				path, *args = args
				Image.fromarray(await client.screenshot()).convert("RGB").save(path)
			elif action in ("click", "dclick", "rclick"):
				x, y, *args = args
				client.mouse.move(int(x), int(y))
				await asyncio.sleep(0.2)
				if action == "rclick":
					client.mouse.right_click()
				else:
					for _ in range(2 if action == "dclick" else 1):
						with client.mouse.hold():
							await asyncio.sleep(0.08)
						await asyncio.sleep(0.08)
			elif action == "type":
				text, *args = args
				client.keyboard.write(text)
			elif action == "drag":
				x1, y1, x2, y2, *args = args
				client.mouse.move(int(x1), int(y1))
				await asyncio.sleep(0.2)
				with client.mouse.hold():
					for i in range(1, 11):
						client.mouse.move(int(x1) + (int(x2) - int(x1)) * i // 10, int(y1) + (int(y2) - int(y1)) * i // 10)
						await asyncio.sleep(0.05)
			elif action == "key":
				combo, *args = args
				*mods, key = combo.split("+")
				with client.keyboard.hold(*mods):
					client.keyboard.press(key)
			elif action == "scroll":
				x, y, direction, *args = args
				client.mouse.move(int(x), int(y))
				(client.mouse.scroll_up if direction == "up" else client.mouse.scroll_down)()
			elif action == "sleep":
				seconds, *args = args
				await asyncio.sleep(float(seconds))
			else:
				sys.exit(f"unknown action {action}")
			await asyncio.sleep(0.6)


asyncio.run(run(sys.argv[1:]))
