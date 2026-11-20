"""CLI entry point: Test Contract v1.1 and a shared-logic desktop game."""
import argparse
import json
import sys
from pathlib import Path
from src.lantern_island.model import DEFAULT_INPUT, Game, validate_inputs


def load_json(path):
    def reject_constant(value):
        raise ValueError("non-finite JSON number: " + value)
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=reject_constant, object_pairs_hook=unique_keys)


def run_headless(game, frames, ticks, snapshot_every, stream):
    def write(record):
        stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
    controls = dict(DEFAULT_INPUT)
    index = 0
    write(game.snapshot())
    for tick in range(ticks):
        if index < len(frames) and frames[index]["tick"] == tick:
            controls.update({k: v for k, v in frames[index].items() if k != "tick"})
            index += 1
        for event in game.step(controls):
            write(event)
        if game.tick % snapshot_every == 0:
            write(game.snapshot())
        if game.state in ("won", "lost"):
            break
    write(dict(type="end", ticks=game.tick, state=game.state, score=game.score))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Đảo Đèn Lồng · Test Contract v1.1")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--seed", type=int, default=12)
    parser.add_argument("--night", type=int, choices=[1,2,3], default=1)
    parser.add_argument("--scenario", type=Path)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--ticks", type=int)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--snapshot-every", type=int, default=10)
    args = parser.parse_args(argv)
    if args.headless:
        if args.ticks is None or args.ticks < 0 or args.out is None or args.snapshot_every <= 0:
            parser.error("headless requires --ticks >= 0, --out, and --snapshot-every > 0")
        try:
            scenario = load_json(args.scenario) if args.scenario else None
            frames = validate_inputs(load_json(args.inputs)) if args.inputs else []
            game = Game(args.seed, scenario, args.night)
        except (OSError, ValueError, TypeError, OverflowError) as error:
            print("Invalid inputs/scenario: " + str(error), file=sys.stderr)
            return 2
        try:
            with args.out.open("w", encoding="utf-8", newline="\n") as stream:
                run_headless(game, frames, args.ticks, args.snapshot_every, stream)
        except (OSError, ValueError) as error:
            print("Headless failed: " + str(error), file=sys.stderr)
            return 1
    else:
        if args.inputs or args.scenario or args.out or args.ticks is not None:
            parser.error("scenario/inputs/ticks/out require --headless")
        try:
            from src.lantern_island.view import play
            play(args.seed)
        except ImportError as error:
            print("Desktop runtime missing: run python3 tools/build.py. " + str(error), file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
