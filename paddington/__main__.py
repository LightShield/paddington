import argparse
from pathlib import Path
from .analysis import analyze_files
from .optimization import optimize_files


def main():
    parser = argparse.ArgumentParser(
        description="paddingTON - padding Trimming Optimization eNgine"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze structs for padding waste"
    )
    analyze_parser.add_argument("path", type=Path, help="File or directory to analyze")
    analyze_parser.add_argument(
        "-v", "--verbose", action="count", default=1, help="Increase verbosity"
    )

    # optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Optimize struct padding")
    optimize_parser.add_argument(
        "path", type=Path, help="File or directory to optimize"
    )
    optimize_parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default: dry-run)"
    )
    optimize_parser.add_argument(
        "--force", action="store_true", help="Reorder even if no size savings"
    )
    optimize_parser.add_argument(
        "--update-signatures",
        action="store_true",
        help="Update constructor signatures and call sites (default: only update initializer lists)",
    )
    optimize_parser.add_argument(
        "--patch-dir",
        type=Path,
        help="Generate git patches instead of modifying files",
    )
    optimize_parser.add_argument(
        "--build-command",
        type=str,
        help="Command to run after each optimization to verify build (e.g., 'make test')",
    )
    optimize_parser.add_argument(
        "--verify",
        action="store_true",
        help="Use compilation database to verify each file compiles (requires compile_commands.json)",
    )
    optimize_parser.add_argument(
        "-v", "--verbose", action="count", default=1, help="Increase verbosity"
    )

    args = parser.parse_args()

    if args.command == "analyze":
        analyze_files(args.path, verbosity=args.verbose)
    elif args.command == "optimize":
        optimize_files(
            args.path,
            dry_run=not args.apply,
            force=args.force,
            update_signatures=args.update_signatures,
            patch_dir=args.patch_dir,
            build_command=args.build_command,
            verify=args.verify,
            verbosity=args.verbose,
        )


if __name__ == "__main__":
    main()
