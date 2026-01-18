"""Entry point for paddingTON CLI."""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="paddingTON - C++ struct padding optimizer (dry-run by default)"
    )
    
    # Main arguments (optimize is the only/default command)
    parser.add_argument("path", type=Path, help="Path to object files or directory")
    parser.add_argument("--apply", action="store_true",
                         help="Apply changes (default: dry-run)")
    parser.add_argument("--min-savings", type=int, default=0,
                         help="Minimum bytes to optimize (default: 0)")
    parser.add_argument("--access-modifier-strategy",
                         choices=["preserve", "split", "ignore"],
                         default="preserve",
                         help="How to handle access modifiers (default: preserve)")
    parser.add_argument("--extractor", choices=["pahole", "dwarf"],
                         default="dwarf", help="Extraction method")
    parser.add_argument("--transformer", choices=["srcml", "line-swap"],
                         default="srcml", help="Transformation method (default: srcml)")
    parser.add_argument("--output", choices=["patch", "file"],
                         default="patch", help="Output method")
    parser.add_argument("--patch-dir", type=Path, default=Path("./patches"),
                         help="Directory for patches (default: ./patches)")
    parser.add_argument("--include", action="append", help="Include file pattern")
    parser.add_argument("--exclude", action="append", help="Exclude file pattern")
    parser.add_argument("--struct-names", action="append", help="Only optimize specific struct names")
    parser.add_argument("-v", "--verbose", action="count", default=1,
                         help="Increase verbosity (-v, -vv, -vvv)")
    
    args = parser.parse_args()
    
    # Run optimize
    from implementation.user_interactions import optimize
    sys.exit(optimize.run(args))


if __name__ == "__main__":
    main()
