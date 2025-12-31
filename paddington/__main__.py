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
    analyze_parser.add_argument("path", type=Path, help="Object file or directory to analyze")
    analyze_parser.add_argument(
        "--include",
        type=str,
        action="append",
        help="Only process files matching pattern (can be used multiple times)",
    )
    analyze_parser.add_argument(
        "--exclude",
        type=str,
        action="append",
        help="Skip files matching pattern (can be used multiple times)",
    )
    analyze_parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Directory for caching parsed .o files (speeds up re-runs)",
    )
    analyze_parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Deduplicate .o files by content hash before processing",
    )
    analyze_parser.add_argument(
        "--use-pahole",
        action="store_true",
        help="Use pahole instead of pyelftools (100x faster, requires pahole installed)",
    )
    analyze_parser.add_argument(
        "-v", "--verbose", action="count", default=1, help="Increase verbosity"
    )

    # optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Optimize struct padding")
    optimize_parser.add_argument(
        "path", type=Path, help="Object file or directory to optimize"
    )
    optimize_parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default: dry-run)"
    )
    optimize_parser.add_argument(
        "--force", action="store_true", help="Reorder even if no size savings"
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
        help="Verify compilation after changes",
    )
    optimize_parser.add_argument(
        "--include",
        type=str,
        action="append",
        help="Only process files matching pattern (can be used multiple times)",
    )
    optimize_parser.add_argument(
        "--exclude",
        type=str,
        action="append",
        help="Skip files matching pattern (can be used multiple times)",
    )
    optimize_parser.add_argument(
        "--remap-from",
        type=str,
        help="Path prefix to replace (for dev environments)",
    )
    optimize_parser.add_argument(
        "--remap-to",
        type=str,
        help="New path prefix (for dev environments)",
    )
    optimize_parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Directory for caching parsed .o files (speeds up re-runs)",
    )
    optimize_parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Deduplicate .o files by content hash before processing",
    )
    optimize_parser.add_argument(
        "--use-pahole",
        action="store_true",
        help="Use pahole instead of pyelftools (100x faster, requires pahole installed)",
    )
    optimize_parser.add_argument(
        "--compile-commands",
        type=str,
        help="Path to directory containing compile_commands.json (enables clang-based rewriting)",
    )
    optimize_parser.add_argument(
        "-v", "--verbose", action="count", default=1, help="Increase verbosity"
    )

    args = parser.parse_args()

    if args.command == "analyze":
        analyze_files(
            args.path,
            include_patterns=args.include,
            exclude_patterns=args.exclude,
            cache_dir=args.cache_dir,
            deduplicate=args.deduplicate,
            use_pahole=args.use_pahole,
            verbosity=args.verbose,
        )
    elif args.command == "optimize":
        optimize_files(
            args.path,
            dry_run=not args.apply,
            force=args.force,
            patch_dir=args.patch_dir,
            build_command=args.build_command,
            verify=args.verify,
            include_patterns=args.include,
            exclude_patterns=args.exclude,
            remap_from=args.remap_from,
            remap_to=args.remap_to,
            cache_dir=args.cache_dir,
            deduplicate=args.deduplicate,
            use_pahole=args.use_pahole,
            compile_commands=args.compile_commands,
            verbosity=args.verbose,
        )


if __name__ == "__main__":
    main()
