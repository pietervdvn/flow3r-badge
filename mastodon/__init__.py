import leds
import st3m.run
from st3m import logging
from st3m.reactor import Responder

from st3m.application import Application, ApplicationContext
import network

log = logging.Log(__name__, level=logging.INFO)
class Mastodon(Application):

    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)
        self.time = 0
        self.wlan = network.WLAN(network.WIFI_STA)
        self.wlan.active(True)
        self.wlan.connect("Camp2023-open", "")
        self.wlan.connect()


    def draw(self, ctx: Context) -> None:
        pass

    def think(self, ins: InputState, delta_ms: int) -> None:
        # https://en.osm.town/api/v1/timelines/tag/cccamp2023
        self.time = self.time + delta_ms
        if self.time + 15*
            
if __name__ == "__main__":
    st3m.run.run_view(Mastodon(ApplicationContext()))
