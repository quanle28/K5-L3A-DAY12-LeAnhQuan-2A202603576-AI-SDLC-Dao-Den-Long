"""Fixed-step gameplay shared by desktop and Test Contract v1.0 headless mode."""
import json
import math
import random
from pathlib import Path

DT = 1 / 60
ISLAND_RADIUS = 32.0
TUNING = json.loads((Path(__file__).resolve().parents[2] / "game.contract.json").read_text(encoding="utf-8"))["tuning"]


def number(value, label, minimum=None, maximum=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(label + " must be a finite number")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ValueError(label + " is outside allowed range")
    return value


def integer(value, label, minimum=0, maximum=None):
    if type(value) is not int:
        raise ValueError(label + " must be an integer")
    return number(value, label, minimum, maximum)


def boolean(value, label):
    if type(value) is not bool:
        raise ValueError(label + " must be a boolean")
    return value


def fields(obj, allowed, label):
    if not isinstance(obj, dict) or set(obj) - set(allowed):
        raise ValueError(label + " has invalid fields")


def position(value):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError("pos must be [x,y,z]")
    return [number(v, "position") for v in value]


def distance(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


def rounded(pos):
    return [round(float(v), 3) + 0.0 for v in pos]


DEFAULT_INPUT = dict(move=[0, 0], cam_yaw_deg=0, jump=False, interact=False, pulse=False, dash=False)


def validate_inputs(data):
    fields(data, ["frames"], "inputs")
    frames = data.get("frames")
    if not isinstance(frames, list):
        raise ValueError("inputs.frames must be an array")
    previous = -1
    for frame in frames:
        fields(frame, ["tick"] + list(DEFAULT_INPUT), "input frame")
        tick = integer(frame.get("tick"), "frame.tick")
        if tick <= previous:
            raise ValueError("input ticks must increase strictly")
        previous = tick
        if "move" in frame:
            move = frame["move"]
            if not isinstance(move, list) or len(move) != 2:
                raise ValueError("move must be [x,z]")
            for component in move:
                number(component, "move component", -1, 1)
        if "cam_yaw_deg" in frame:
            number(frame["cam_yaw_deg"], "cam_yaw_deg")
        for key in ("jump", "interact", "pulse", "dash"):
            if key in frame:
                boolean(frame[key], key)
    return frames


class Game:
    def __init__(self, seed=12, scenario=None):
        self.rng = random.Random(seed)
        self.tick = 0
        self.state = "playing"
        self.score = 0
        self.pos = [0.0, 0.0, 0.0]
        self.carried = 0
        self.flames = TUNING["flames"]
        self.duration = TUNING["night1_duration_s"]
        self.invuln_until = 0
        self.pulse_ready = 0
        self.vy = 0
        self.previous = dict(DEFAULT_INPUT)
        self.events = []
        self.mote_serial = self.shade_serial = 0
        self.random_motes = self.random_shades = True
        self.lanterns = []
        for i in range(5):
            angle = i * math.tau / 5
            self.lanterns.append(dict(id="L" + str(i + 1),
                                      pos=[21 * math.sin(angle), 0, 21 * math.cos(angle)],
                                      deposited=0, lit=False))
        self.motes = []
        self.shades = []
        self._scenario({} if scenario is None else scenario)

    @property
    def time_left(self):
        return self.duration - self.tick * DT

    def _new_mote(self, pos):
        self.mote_serial += 1
        self.motes.append(dict(id="M" + str(self.mote_serial), pos=list(pos)))

    def _random_point(self, outer=29):
        a = self.rng.random() * math.tau
        r = math.sqrt(self.rng.random()) * outer
        return [math.sin(a) * r, 0.0, math.cos(a) * r]

    def _new_shade(self, pos, identifier=None):
        if identifier is None:
            while True:
                self.shade_serial += 1
                identifier = "S" + str(self.shade_serial)
                if all(e["id"] != identifier for e in self.shades):
                    break
        self.shades.append(dict(id=identifier, pos=list(pos), state="chase", stunned_until=0))
        return identifier

    def _scenario(self, data):
        fields(data, ["player", "random_motes", "random_shades", "motes", "shades", "lanterns", "time_left_s"], "scenario")
        self.random_motes = boolean(data.get("random_motes", True), "random_motes")
        self.random_shades = boolean(data.get("random_shades", True), "random_shades")
        p = data.get("player", {})
        fields(p, ["pos", "carried", "flames"], "player")
        self.pos = position(p.get("pos", [0, 0, 0]))
        self.carried = integer(p.get("carried", 0), "carried", 0, TUNING["carry_capacity"])
        self.flames = integer(p.get("flames", TUNING["flames"]), "flames", 0, TUNING["flames"])
        self.duration = number(data.get("time_left_s", self.duration), "time_left_s", 0)
        for key in ("motes", "shades", "lanterns"):
            if key in data and not isinstance(data[key], list):
                raise ValueError(key + " must be an array")
        if "motes" in data:
            for pos in data["motes"]:
                self._new_mote(position(pos))
        elif self.random_motes:
            for lamp in self.lanterns:
                for j in range(1, 11):
                    self._new_mote([lamp["pos"][0] * j / 11, 0, lamp["pos"][2] * j / 11])
            for _ in range(25):
                self._new_mote(self._random_point())
        if "shades" in data:
            for shade in data["shades"]:
                fields(shade, ["id", "pos"], "shade")
                identifier = shade.get("id")
                if "id" in shade and (not isinstance(identifier, str) or not identifier):
                    raise ValueError("shade id must be a nonempty string")
                if identifier is not None and any(e["id"] == identifier for e in self.shades):
                    raise ValueError("duplicate shade id")
                self._new_shade(position(shade.get("pos")), identifier)
        elif self.random_shades:
            for a in (.5, 2.7, 4.8):
                self._new_shade([28 * math.sin(a), .7, 28 * math.cos(a)])
        seen = set()
        for update in data.get("lanterns", []):
            fields(update, ["id", "pos", "deposited", "lit"], "lantern")
            identifier = update.get("id")
            if not isinstance(identifier, str) or identifier in seen:
                raise ValueError("invalid or duplicate lantern id")
            lamps = [e for e in self.lanterns if e["id"] == identifier]
            if not lamps:
                raise ValueError("unknown lantern id: " + identifier)
            seen.add(identifier)
            lamp = lamps[0]
            if "pos" in update:
                lamp["pos"] = position(update["pos"])
            deposited = integer(update.get("deposited", 0), "deposited", 0, TUNING["lantern_cost"])
            lit = boolean(update.get("lit", False), "lit")
            lamp["lit"] = lit or deposited == TUNING["lantern_cost"]
            lamp["deposited"] = TUNING["lantern_cost"] if lamp["lit"] else deposited


    def emit(self, name, **data):
        self.events.append(dict(type="event", tick=self.tick, name=name, data=data))

    def _finish(self, state, reason):
        self.state = state
        if state == "won":
            self.score += math.floor(max(0, self.time_left)) * TUNING["score"]["per_second_left"]
            self.score += self.flames * TUNING["score"]["per_flame_left"]
        self.emit("game_over", result=state, reason=reason)

    def _outside_lights(self, pos):
        for _ in range(8):
            changed = False
            for lamp in self.lanterns:
                if not lamp["lit"]:
                    continue
                d = distance(pos, lamp["pos"])
                r = TUNING["safe_radius"]
                if d < r:
                    dx, dz = pos[0] - lamp["pos"][0], pos[2] - lamp["pos"][2]
                    if d < 1e-12:
                        dx, dz, d = 1.0, 0.0, 1.0
                    pos[0] = lamp["pos"][0] + dx / d * (r + .00001)
                    pos[2] = lamp["pos"][2] + dz / d * (r + .00001)
                    changed = True
            if not changed:
                break

    def step(self, controls=None):
        if self.state != "playing":
            return []
        controls = dict(DEFAULT_INPUT if controls is None else controls)
        self.tick += 1
        self.events = []
        pressed = {key: controls.get(key, False) and not self.previous.get(key, False)
                   for key in ("jump", "interact", "pulse")}
        self.previous = dict(controls)
        x, z = controls.get("move", [0, 0])
        length = max(1, math.hypot(x, z))
        x, z = x / length, z / length
        yaw = math.radians(controls.get("cam_yaw_deg", 0) % 360)
        self.pos[0] += (x * math.cos(yaw) + z * math.sin(yaw)) * TUNING["player_speed"] * DT
        self.pos[2] += (-x * math.sin(yaw) + z * math.cos(yaw)) * TUNING["player_speed"] * DT
        r = math.hypot(self.pos[0], self.pos[2])
        if r > ISLAND_RADIUS:
            self.pos[0] *= ISLAND_RADIUS / r
            self.pos[2] *= ISLAND_RADIUS / r
        if pressed["jump"] and self.pos[1] <= 0:
            self.vy = 7
        if self.pos[1] > 0 or self.vy > 0:
            self.pos[1] = max(0, self.pos[1] + self.vy * DT)
            self.vy -= 18 * DT
            if self.pos[1] == 0:
                self.vy = 0
        remaining = []
        for mote in self.motes:
            if self.carried < TUNING["carry_capacity"] and distance(self.pos, mote["pos"]) <= TUNING["pickup_radius"]:
                self.carried += 1
                self.score += TUNING["score"]["per_mote"]
                self.emit("mote_picked", carried=self.carried)
            else:
                remaining.append(mote)
        self.motes = remaining
        if pressed["interact"]:
            nearby = [lamp for lamp in self.lanterns if not lamp["lit"] and
                      distance(self.pos, lamp["pos"]) <= TUNING["interact_radius"]]
            if nearby and self.carried:
                lamp = min(nearby, key=lambda e: (distance(self.pos, e["pos"]), e["id"]))
                amount = min(self.carried, TUNING["lantern_cost"] - lamp["deposited"])
                self.carried -= amount
                lamp["deposited"] += amount
                self.emit("deposit", lantern_id=lamp["id"], amount=amount, deposited=lamp["deposited"])
                if lamp["deposited"] == TUNING["lantern_cost"]:
                    lamp["lit"] = True
                    self.score += TUNING["score"]["per_lantern"]
                    self.emit("lantern_lit", lantern_id=lamp["id"])
        if pressed["pulse"] and self.carried >= TUNING["pulse_cost"] and self.tick >= self.pulse_ready:
            self.carried -= TUNING["pulse_cost"]
            self.pulse_ready = self.tick + round(TUNING["pulse_cooldown_s"] * 60)
            stunned = []
            for shade in self.shades:
                d = distance(self.pos, shade["pos"])
                if d <= TUNING["pulse_radius"]:
                    shade["state"] = "stunned"
                    shade["stunned_until"] = self.tick + round(TUNING["pulse_stun_s"] * 60)
                    dx, dz = shade["pos"][0] - self.pos[0], shade["pos"][2] - self.pos[2]
                    if d < 1e-12:
                        dx, dz, d = 1, 0, 1
                    shade["pos"][0] += dx / d * TUNING["pulse_push_m"]
                    shade["pos"][2] += dz / d * TUNING["pulse_push_m"]
                    stunned.append(shade["id"])
                    self.score += TUNING["score"]["per_stun"]
            self.emit("pulse", stunned_ids=stunned)
        for shade in self.shades:
            self._outside_lights(shade["pos"])
            if self.tick < shade["stunned_until"]:
                shade["state"] = "stunned"
                continue
            shade["state"] = "chase"
            d = distance(self.pos, shade["pos"])
            if d > 0:
                amount = min(d, TUNING["shade_speed"] * DT)
                candidate = list(shade["pos"])
                candidate[0] += (self.pos[0] - candidate[0]) / d * amount
                candidate[2] += (self.pos[2] - candidate[2]) / d * amount
                self._outside_lights(candidate)
                shade["pos"] = candidate
        if all(lamp["lit"] for lamp in self.lanterns):
            self._finish("won", "all_lit")
        else:
            safe = any(lamp["lit"] and distance(self.pos, lamp["pos"]) <= TUNING["safe_radius"] for lamp in self.lanterns)
            hit = any(s["state"] != "stunned" and distance(self.pos, s["pos"]) <= TUNING["shade_hit_radius"] for s in self.shades)
            if not safe and hit and self.tick >= self.invuln_until and self.flames > 0:
                self.flames -= 1
                dropped = math.floor(self.carried * TUNING["hit_drop_ratio"])
                self.carried -= dropped
                self.invuln_until = self.tick + round(TUNING["invuln_s"] * 60)
                self.emit("player_hit", by="shade", flames=self.flames, dropped=dropped)
            if self.flames <= 0:
                self._finish("lost", "no_flames")
            elif self.time_left <= 0:
                self._finish("lost", "dawn")
        if self.state == "playing":
            if self.random_motes and self.tick % 60 == 0 and len(self.motes) < 100:
                self._new_mote(self._random_point())
            if self.random_shades and self.tick % 720 == 0 and len(self.shades) < 12:
                a = self.rng.random() * math.tau
                identifier = self._new_shade([31 * math.sin(a), .7, 31 * math.cos(a)])
                self._outside_lights(self.shades[-1]["pos"])
                self.emit("shade_spawned", id=identifier)
        return self.events

    def snapshot(self):
        return dict(type="snapshot", tick=self.tick, sim_tick=self.tick, state=self.state,
                    time_left_s=self.time_left, score=self.score,
                    player=dict(pos=rounded(self.pos), flames=self.flames, carried=self.carried),
                    lanterns=[dict(id=e["id"], pos=rounded(e["pos"]), lit=e["lit"], deposited=e["deposited"]) for e in self.lanterns],
                    shades=[dict(id=e["id"], pos=rounded(e["pos"]), state=e["state"]) for e in self.shades],
                    motes_active=len(self.motes), motes=[dict(id=e["id"], pos=rounded(e["pos"])) for e in self.motes])
