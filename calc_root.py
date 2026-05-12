#!/usr/bin/env python3
import argparse
import hashlib

def calc_root_password(devid: str, ctx: str, pass_mp: str, pass_up: str) -> str:
        if devid.startswith("166"):
                material = f"{devid}{ctx}{pass_up}"
        else:
                material = f"{devid}{ctx}{pass_mp}{pass_up}"
        return hashlib.md5(material.encode("utf-8")).hexdigest()

def main():
        p = argparse.ArgumentParser(description="Calculate firmware root password")
        p.add_argument("--devid", required=True, help="Device ID / SN")
        p.add_argument("--ctx", required=True, help="ctx value (e.g. 7841 or debug)")
        p.add_argument("--pass-mp", default="", help="pass.mp value")
        p.add_argument("--pass-up", required=True, help="pass.up value")
        args = p.parse_args()

        root = calc_root_password(args.devid, args.ctx, args.pass_mp, args.pass_up)
        print(root)

if __name__ == "__main__":
        main()
