"""Entry point for paddingTON CLI."""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="paddingTON - C++ struct padding optimizer"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze C++ structs for padding waste"
    )
    analyze_parser.add_argument("path", type=Path, help="Path to object files or directory")
    analyze_parser.add_argument("--include", action="append", help="Include file pattern")
    analyze_parser.add_argument("--exclude", action="append", help="Exclude file pattern")
    analyze_parser.add_argument("--extractor", choices=["pahole", "dwarf"], 
                                default="dwarf", help="Extraction method")
    analyze_parser.add_argument("-v", "--verbose", action="count", default=1,
                                help="Increase verbosity (-v, -vv, -vvv)")
    
    # optimize command
    optimize_parser = subparsers.add_parser(
        "optimize",
        help="Optimize C++ structs to minimize padding"
    )
    optimize_parser.add_argument("path", type=Path, help="Path to object files or directory")
    optimize_parser.add_argument("--apply", action="store_true",
                                 help="Apply changes (default: dry-run)")
    optimize_parser.add_argument("--min-savings", type=int, default=0,
                                 help="Minimum bytes to optimize (default: 0)")
    optimize_parser.add_argument("--access-modifier-strategy",
                                 choices=["preserve", "split", "ignore"],
                                 default="preserve",
                                 help="How to handle access modifiers (default: preserve)")
    optimize_parser.add_argument("--extractor", choices=["pahole", "dwarf"],
                                 default="dwarf", help="Extraction method")
    optimize_parser.add_argument("--transformer", choices=["srcml", "line-swap"],
                                 default="line-swap", help="Transformation method")
    optimize_parser.add_argument("--output", choices=["patch", "file"],
                                 default="patch", help="Output method")
    optimize_parser.add_argument("--patch-dir", type=Path, default=Path("./patches"),
                                 help="Directory for patches (default: ./patches)")
    optimize_parser.add_argument("--include", action="append", help="Include file pattern")
    optimize_parser.add_argument("--exclude", action="append", help="Exclude file pattern")
    optimize_parser.add_argument("-v", "--verbose", action="count", default=1,
                                 help="Increase verbosity (-v, -vv, -vvv)")
    
    args = parser.parse_args()
    
    # Dispatch to command
    if args.command == "analyze":
        from implementation.user_interactions import analyze
        sys.exit(analyze.run(args))
    elif args.command == "optimize":
        from implementation.user_interactions import optimize
        sys.exit(optimize.run(args))


if __name__ == "__main__":
    main()
