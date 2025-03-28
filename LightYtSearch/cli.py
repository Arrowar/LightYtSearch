"""
Command-line interface for LightYtSearch package.
"""

import json
import argparse

from .core import search_youtube
from .version import __version__
from .utils import colors

def main():
    parser = argparse.ArgumentParser(description="Lightweight YouTube search scraper")

    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--max-results", type=int, default=5, help="Maximum number of results (default: 5, max: 20)")
    parser.add_argument("-j", "--json", action="store_true", help="Output results as JSON")
    parser.add_argument("-s", "--save", action="store_true", help="Save results to a file")
    parser.add_argument("-o", "--output", help="Output filename (default: results.json)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (minimal output)")
    parser.add_argument("-v", "--version", action="store_true", help="Show version information")
    parser.add_argument("--filter", choices=["video", "playlist", "movie"], help="Filter results by type")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
    parser.add_argument("--language", default="en", help="Language code (default: en)")
    parser.add_argument("--region", default="US", help="Region code (default: US)")
    parser.add_argument("--retry-count", type=int, default=3, help="Number of retries for failed requests (default: 3)")
    parser.add_argument("--retry-delay", type=int, default=2, help="Delay between retries in seconds (default: 2)")
    parser.add_argument("--time", action="store_true", help="Show execution time for each process")
    parser.add_argument('--save-raw-data', action='store_true', help='Save raw YouTube data to JSON file')
    parser.add_argument('--raw-data-dir', type=str, default=None, help='Directory to save raw YouTube data (default: ./raw_data)')
    
    args = parser.parse_args()
    
    if args.version:
        print(f"{colors.fg.purple}LightYtSearch{colors.reset} v{colors.fg.cyan}{__version__}{colors.reset}")
        return None
    
    save_raw_data = args.save_raw_data
    
    results = search_youtube(
        query=args.query,
        max_results=args.max_results,
        filter_type=args.filter,
        timeout=args.timeout,
        language=args.language,
        region=args.region,
        save_json=args.save,
        output_file=args.output,
        verbose=not args.quiet,
        showResults=not args.json and not args.quiet,
        retry_count=args.retry_count,
        retry_delay=args.retry_delay,
        showTimeExecution=args.time,
        save_raw_data=save_raw_data,
        raw_data_dir=args.raw_data_dir
    )
    
    if args.json:
        print(json.dumps(results, indent=2))
    elif not args.quiet:
        pass
    
    return results

if __name__ == "__main__":
    main()