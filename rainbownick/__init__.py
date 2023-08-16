import leds
import network
import st3m.run
from st3m import logging
from st3m.reactor import Responder

from st3m.application import Application, ApplicationContext

log = logging.Log(__name__, level=logging.INFO)
log.info("Hello world!")

rainbow = [[0xe5 / 256, 0, 0],
           [0xff / 256, 0x8d / 256, 0],
           [0xff / 256, 0xee / 256, 0],
           [0x02 / 256, 0x81 / 256, 0x21 / 256],
           [0x00 / 256, 0x4c / 256, 0xff / 256],
           [0x77 / 256, 0x00 / 256, 0x88 / 256],
           ]


class RainbowNick(Application):

    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)
        self._x = -20
        try:
            self.wlan = network.WLAN(network.STA_IF)
            self.wlan.active(True),
            self.wlan.connect("Camp2023-open", "")
        except:
            log.error("Wifi error")
        self.time = 0
        self.current_led = -1
        self.pos = 0

    def draw(self, ctx: Context) -> None:

        leds.set_all_rgb(0, 0, 0)
        i = (self.time * 10 // 10000) % 10000
        if self.current_led != i:
            log.info("Led:" + str(i))
            for ix in range(0, 7):
                color = rainbow[ix % len(rainbow)]
                band = 5
                for offset in range(0, band):
                    leds.set_rgb((i + ix * band + offset) % 40, color[0], color[1], color[2])
            #if not self.wlan.isconnected():
            #    leds.set_rgb(i, 1.0, 0.0, 0.0)
            #    log.info("Still not connected")
            #    return
            leds.update()
            self.current_led = i

        ctx.save()
        ctx.image_smoothing = False

        nr_colors = len(rainbow)
        stripe = 240 / nr_colors
        idx = int(self.pos / stripe)
        yoff = self.pos % stripe

        # center of screen is [0, 0]
        # x goes right, y goes down -> bottom left is [-120, +120]

        r = 2 * 3.1415 * ((self.time % (1000*10)) / (1000*10))
        ctx.rotate(r)

        for i in range(nr_colors + 1):
            col = rainbow[(idx - i) % nr_colors]
            ctx.rectangle(-120, +120 - yoff - stripe * i, 240, stripe)
            ctx.rgb(col[0], col[1], col[2])
            ctx.fill()

        ctx.rotate(-r)
        ctx.move_to(0, 0)
        ctx.rgb(1,1,1)
        ctx.rectangle(0, 50, 0, 50)
        ctx.fill()
        # Paint a red square in the middle of the display
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.font_size = 60
        ctx.font = ctx.get_font_name(5)

        ctx.rgb(0, 0, 0)
        ctx.text("pietervdvn")
        ctx.restore()

    def think(self, ins: InputState, delta_ms: int) -> None:
        self.time = self.time + delta_ms
        direction = ins.buttons.app

        if direction == ins.buttons.PRESSED_LEFT:
            self._x -= 1
        elif direction == ins.buttons.PRESSED_RIGHT:
            self._x += 1

if __name__ == "__main__":
    st3m.run.run_view(RainbowNick(ApplicationContext()))
