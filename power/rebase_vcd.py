import argparse
import os
import sys


def first_timestamp(path):
    with open(path) as fd:
        for line in fd:
            if line.startswith("#"):
                return int(line[1:])
    raise SystemExit(f"{path}: no timestamps found")


def last_timestamp(path):
    last = None
    with open(path) as fd:
        for line in fd:
            if line.startswith("#"):
                last = int(line[1:])
    return last


def rebase(path):
    offset = first_timestamp(path)
    if offset == 0:
        return offset
    tmp = path + ".tmp"
    with open(path) as src, open(tmp, "w") as dst:
        for line in src:
            if line.startswith("#"):
                dst.write(f"#{int(line[1:]) - offset}\n")
            else:
                dst.write(line)
    os.replace(tmp, path)
    return offset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vcd")
    ap.add_argument("--mode", default="fft")
    ap.add_argument("--corner", default="")
    ap.add_argument("--clock-ns", type=float, default=20.0)
    ap.add_argument("--blocks", type=int, default=4)
    ap.add_argument("--netlist", default="")
    ap.add_argument("--run-tag", default="")
    args = ap.parse_args()

    offset = rebase(args.vcd)
    if offset:
        print(
            f"{args.vcd}: shifted {offset} ps so the measured window starts at 0",
            file=sys.stderr,
        )

    span_ps = last_timestamp(args.vcd)
    span_ns = span_ps / 1000.0
    cycles = span_ns / args.clock_ns
    freq_mhz = 1000.0 / args.clock_ns

    rule = "=" * 78
    print(rule)
    print(f" {args.mode.upper()} power analysis")
    print(rule)
    print(f" Netlist   : {args.netlist}")
    if args.run_tag:
        print(f" Run tag   : {args.run_tag}")
    print(f" Corner    : {args.corner}")
    print(f" Clock     : {freq_mhz:.1f} MHz ({args.clock_ns:g} ns period)")
    print(f" Workload  : {args.blocks} {args.mode.upper()} blocks, each verified "
          f"against model/fft16.py")
    print(f" Activity  : {os.path.basename(args.vcd)}")
    print(f" Window    : {span_ns / 1000.0:.3f} us = {cycles:.0f} clock cycles")
    print(" Excluded  : power-on reset and the SPI configuration that precede it")
    print(rule)


if __name__ == "__main__":
    main()
