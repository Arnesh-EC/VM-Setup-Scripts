"""Shared helpers for the CLI front-ends."""

import argparse
import getpass
import sys


def arg_validator(fn):
    """Adapt a library validator (raises ValueError / ValidationError) into an
    argparse ``type=``, preserving the message. Works for both configgen and
    vmkit validators (both raise ValueError subclasses), keeping the libraries
    free of any argparse dependency.
    """

    def _type(value):
        try:
            return fn(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(str(exc))

    _type.__name__ = getattr(fn, "__name__", "value")
    return _type


def add_connection_args(parser: argparse.ArgumentParser) -> None:
    """Add the shared ESXi connection options (-s/-u/-p/-P)."""
    parser.add_argument("-s", "--server", required=True, metavar="HOST",
                        help="ESXi host FQDN or IP.")
    parser.add_argument("-u", "--user", required=True, metavar="USER",
                        help="ESXi username.")
    parser.add_argument("-p", "--password", default=None, metavar="PASS",
                        help="ESXi password. If omitted, prompts securely.")
    parser.add_argument("-P", "--port", type=int, default=443, metavar="PORT",
                        help="HTTPS port (default: 443).")


def resolve_password(args: argparse.Namespace) -> str:
    """Return the password from args, or prompt securely. Exits 130 on cancel."""
    if args.password:
        return args.password
    try:
        return getpass.getpass(
            f"Password for {args.user}@{args.server}: ", echo_char="*"
        )
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(130)
