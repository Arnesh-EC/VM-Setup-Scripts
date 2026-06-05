#!/usr/bin/env python3
"""
gen_ws_config_iso.py — Generate a vmconfig.json ISO for post-sysprep VM configuration.

Creates an ISO 9660 image containing a single vmconfig.json file. The JSON is read
by FirstBoot.ps1 inside the sysprepped VM to configure hostname, IP, and DNS.

Examples:
  ./gen_ws_config_iso.py -n dc01 --ip 192.168.1.50 --prefix 24 --gateway 192.168.1.1 --dns1 192.168.1.10
  ./gen_ws_config_iso.py -n dc01 --ip 192.168.1.50 --prefix 24 --gateway 192.168.1.1 \\
      --dns1 192.168.1.10 --dns2 8.8.8.8 --dns-suffix corp.example.com -o isos/dc01-config.iso
"""

import argparse
import io
import json
from pathlib import Path

import pycdlib

from vmlib.validate import validate_hostname_rfc, validate_ipv4, validate_prefix


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gen_ws_config_iso.py",
        description=(
            "Generate an ISO containing vmconfig.json for post-sysprep VM configuration.\n\n"
            "The ISO is attached as a CD-ROM in the VMX. FirstBoot.ps1 reads the JSON\n"
            "to configure hostname, static IP, prefix, gateway, and DNS."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s -n dc01 --ip 192.168.1.50 --prefix 24 "
            "--gateway 192.168.1.1 --dns1 192.168.1.10\n"
            "  %(prog)s -n dc01 --ip 192.168.1.50 --prefix 24 "
            "--gateway 192.168.1.1 --dns1 192.168.1.10 \\\n"
            "      --dns2 8.8.8.8 --dns-suffix corp.example.com"
        ),
    )
    parser.add_argument(
        "-n",
        "--hostname",
        required=True,
        type=validate_hostname_rfc,
        metavar="HOSTNAME",
        help="VM hostname (RFC 1123).",
    )
    parser.add_argument(
        "--ip",
        required=True,
        type=validate_ipv4,
        metavar="ADDR",
        help="Static IPv4 address (dotted-quad).",
    )
    parser.add_argument(
        "--prefix",
        required=True,
        type=validate_prefix,
        metavar="LEN",
        help="Subnet prefix length (1–32).",
    )
    parser.add_argument(
        "--gateway",
        required=True,
        type=validate_ipv4,
        metavar="ADDR",
        help="Default gateway IPv4 address.",
    )
    parser.add_argument(
        "--dns1",
        required=True,
        type=validate_ipv4,
        metavar="ADDR",
        help="Primary DNS server IPv4 address.",
    )
    parser.add_argument(
        "--dns2",
        default=None,
        type=validate_ipv4,
        metavar="ADDR",
        help="Secondary DNS server IPv4 address (optional).",
    )
    parser.add_argument(
        "--dns-suffix",
        default=None,
        metavar="SUFFIX",
        help="DNS search suffix, e.g. corp.example.com (optional).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        metavar="FILE",
        help="Output ISO path. Defaults to isos/{hostname}-config.iso.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_path = Path(args.output or Path("isos") / f"{args.hostname}-config.iso")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "hostname": args.hostname,
        "ip": args.ip,
        "prefix": args.prefix,
        "gateway": args.gateway,
        "dns1": args.dns1,
    }
    if args.dns2 is not None:
        config["dns2"] = args.dns2
    if args.dns_suffix is not None:
        config["dns_suffix"] = args.dns_suffix

    json_bytes = json.dumps(config, indent=2).encode("utf-8")

    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=2)
    iso.add_fp(
        io.BytesIO(json_bytes),
        len(json_bytes),
        "/VMCONFIG.JSON;1",
    )
    iso.write(str(output_path))
    iso.close()

    print(f"ISO written to: {output_path}")
    print(f"  hostname    = {args.hostname}")
    print(f"  ip/prefix   = {args.ip}/{args.prefix}")
    print(f"  gateway     = {args.gateway}")
    print(f"  dns1        = {args.dns1}")
    if args.dns2 is not None:
        print(f"  dns2        = {args.dns2}")
    if args.dns_suffix is not None:
        print(f"  dns-suffix  = {args.dns_suffix}")


if __name__ == "__main__":
    main()
