import leds
import st3m.run
from st3m import logging
from st3m.reactor import Responder
from st3m.input import InputController
import json
import network
import ujson
import urequests
from st3m.ui.view import View

from st3m.application import Application, ApplicationContext

log = logging.Log(__name__, level=logging.INFO)


class TrafficLight:
    traffic_light_mode_names = [
    "OFF",
    "GREEN",
    "ORANGE",
    "RED",
    "GREEN_ORANGE",
    "GREEN_RED",
    "ORANGE_RED",
    "ALL",
    "TRAFFIC_LIGHT",
    "ORANGE_FLASHING",
    "TILT",
    "BINARY_CLOCK",
    "TRAFFIC_LIGHT_WARN"
    ]
    current_mode = 0

    def __init__(self, name, ip, supportedModes = None):
        self.name = name
        self.ip = ip
        self.supportedModes = supportedModes

    def toScreen(self):
        return self.name + " is:"

    def getMode(self):
        mode = self.traffic_light_mode_names[self.current_mode]
        return mode.lower().replace("_"," ")

    def cycleMode(self, delta = 1):
        if(delta != 1 and delta != -1):
            raise("Invalid delta")
        self.current_mode += delta
        if(self.current_mode < 0):
            self.current_mode = len(self.traffic_light_mode_names) - 1
        if(self.current_mode >= len(self.traffic_light_mode_names)):
            self.current_mode = 0
        if self.supportedModes is not None and self.current_mode not in self.supportedModes:
            self.cycleMode(delta)

class TrafficLightController(View):

    lights = [
        TrafficLight("Bicycle traffic light", 67),
        TrafficLight("Pedestrian traffic light", 73, [0,1,3,7,8,10,11  ])
    ]

    controlled_entity = 0


    def __init__(self, ip_self) -> None:
        self.input = InputController()
        self._vm = None
        self.ip = str.join(".", map(str, ip_self[0:3] ))# ip_self is a list of four number

    def on_enter(self, vm: Optional[ViewManager]) -> None:
        self._vm = vm
        # Ignore the button which brought us here until it is released
       # self.input._ignore_pressed()


    def _indicatorArrowFor(self, index) -> String :
        if self.controlled_entity == index:
            return "> "
        return "  "

    def draw(self, ctx: Context) -> None:
        # Paint the background black
        ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.font_size = 28
        ctx.font = ctx.get_font_name(5)

        ctx.rgb(1, 1, 1)
        y = -20
        i = 0
        for trafficLight in self.lights:
            ctx.move_to(0, y + i * 50)

            ctx.text(trafficLight.toScreen())
            ctx.move_to(0, y + 20 + i * 50)
            if self.controlled_entity == i:
                ctx.rgb(1,0.5,0.5)
            else:
                ctx.rgb(1,1,1)

            ctx.text(trafficLight.getMode())
            ctx.rgb(1,1,1)

            i += 1



    def think(self, ins: InputState, delta_ms: int) -> None:
        self.input.think(ins, delta_ms) # let the input controller to its magic
        # No need to handle returning back to Example on button press - the
        # flow3r's ViewManager takes care of that automatically.

        light = self.lights[self.controlled_entity]
        if self.input.buttons.app.left.pressed:
            light.cycleMode(-1)
        if self.input.buttons.app.right.pressed:
            light.cycleMode(1)
        try:
            urequests.get("http://"+self.ip+"."+str(light.ip)+"/configure?mode="+str(light.current_mode))
        except Exception as e:
            log.info("Error while setting mode:"+str(e))
        if self.input.buttons.app.middle.pressed:
            self.controlled_entity = (self.controlled_entity + 1) % len(self.lights)



class WLed(Application):

    # mode is 'init', 'connecting_wifi', 'scanning', 'controlling'
    state = "init"

    # bicycle_light or 'pedestrian_light'
    control_mode_target = "bicycle_light"
    # select_light | select_preset
    control_mode = "select_light"

    sta_if = network.WLAN(network.STA_IF)
    ip_self = None
    current_ip_scan = 83
    known_ips = [82,83]

    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)
        self.time = 0
        self.current_led = -1
        self.pos = 0
        self.input = InputController()
        self.leds_brightness = 1

    def drawLeds(self):
        b = self.leds_brightness
        i = (self.time * 10 // 10000) % 10000
        if self.current_led != i:
            for ix in range(0, 6):
                color = rainbow[ix % len(rainbow)]
                band = 6
                for offset in range(0, band):
                    leds.set_rgb((i + ix * band + offset) % 40, b * color[0], b * color[1], b * color[2])
            leds.update()
            self.current_led = i

    def draw(self, ctx: Context) -> None:

        leds.set_all_rgb(0, 0, 0)
        leds.update()

        #ctx.save()
        ctx.image_smoothing = False




        ctx.move_to(0, 0)
        ctx.rgba(0,0,0, 1)
        ctx.rectangle(-120, -120, 240, 240)
        ctx.fill()

        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.font_size = 68
        ctx.font = ctx.get_font_name(5)

        ctx.rgb(1, 1, 1)
        ctx.move_to(0, -20)
        if self.state != "controlling":
            ctx.text(self.state)
        else:
            ctx.text(self.control_mode)

        if self.state == "scanning":
            ctx.font_size = 32
            ctx.move_to(0,40)
            ctx.text("Connecting to")

            ctx.move_to(0,60)
            ctx.text(str.join(".",map(str, self.ip_self[0:2] ) ) + "."+ str(self.current_ip_scan))

        #ctx.restore()


    def on_enter(self, vm: Optional[ViewManager]) -> None:
        self._vm = vm
        self.input._ignore_pressed()

    def think(self, ins: InputState, delta_ms: int) -> None:
        self.input.think(ins, delta_ms) # let the input controller to its magic
        self.time = self.time + delta_ms

        log.info("State is "+self.state)
        sta_if = self.sta_if
        if self.state == "init":
            sta_if.active(True)
            self.state = "connecting_wifi"
            return

        if self.state == 'connecting_wifi':
            log.info("Trying to connect " + str(sta_if.isconnected()) + str(sta_if.ifconfig()))
            if sta_if.isconnected():
                self.ip_self = list(map(int, sta_if.ifconfig()[0].split(".")))
                log.info("Entering traffic light controller")
                self._vm.push(TrafficLightController(self.ip_self))
            return

        if self.state == "scanning":
            ip = self.ip_self.copy()
            if self.current_ip_scan == ip[3] :
                self.current_ip_scan += 1
            ip[3] = self.current_ip_scan
            url = "http://"+str.join(".", map(str,ip)) + "/json"
            log.info("Scanning "+url)
            try:
                response = urequests.get(url, timeout=4)
                json = response.json()
                print(json)
                if json["state"] != Nil:
                    log.info("Probably found a wled entity")
            except Exception as e:
                log.info("Could not get response from "+str(self.current_ip_scan)+" due to "+str(e))
            self.current_ip_scan += 1
            return


st3m.run.run_view(WLed(ApplicationContext()))

# if __name__ == "__main__":
#    st3m.run.run_view(WLed(ApplicationContext()))
