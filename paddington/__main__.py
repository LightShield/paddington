import sys
import argparse
from pathlib import Path
from .analyzer import analyze_files

def main():
    parser = argparse.ArgumentParser(description='paddingTON - padding Trimming Optimization eNgine')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze structs for padding waste')
    analyze_parser.add_argument('path', type=Path, help='File or directory to analyze')
    analyze_parser.add_argument('-v', '--verbose', action='count', default=1, help='Increase verbosity')
    
    # optimize command (placeholder)
    optimize_parser = subparsers.add_parser('optimize', help='Optimize struct padding')
    optimize_parser.add_argument('path', type=Path, help='File or directory to optimize')
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        analyze_files(args.path, verbosity=args.verbose)
    elif args.command == 'optimize':
        print("optimize command not yet implemented")
        sys.exit(1)

if __name__ == '__main__':
    main()
