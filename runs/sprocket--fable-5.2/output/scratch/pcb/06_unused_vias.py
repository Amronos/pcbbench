"""Remove the fan-out vias the autorouter did not use (it reached SD_CMD and SD_CLK on the top layer)."""
from pcblib import *

k, b, doc = open_board()
UNUSED = {'/SD_CMD': (38.0, 17.6), '/SD_CLK': (37.2, 18.15)}
dead = [v for v in b.get_vias() if v.net.name in UNUSED
        and abs(v.position.x / 1e6 - X0 - UNUSED[v.net.name][0]) < 0.01
        and abs(v.position.y / 1e6 - Y0 - UNUSED[v.net.name][1]) < 0.01]
b.remove_items(dead)
b.save()
print('removed', len(dead))
