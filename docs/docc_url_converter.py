#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# ///
"""
DOCC Documentation URL to JSON Converter

Converts DOCC-based documentation URLs to their JSON API format.

Supports:
- Swift.org documentation
- Apple Developer documentation

Examples:
  https://www.swift.org/migration/documentation/migrationguide/
  -> https://www.swift.org/migration/data/documentation/migrationguide.json
  
  https://developer.apple.com/documentation/swift/updating_an_app_to_use_swift_concurrency
  -> https://developer.apple.com/tutorials/data/documentation/swift/updating_an_app_to_use_swift_concurrency.json
"""

import sys
from urllib.parse import urlparse, urlunparse


def convert_docc_url_to_json(url):
    """
    Convert DOCC documentation URL to JSON format.
    
    Args:
        url: The documentation URL (Swift.org or Apple Developer)
        
    Returns:
        The JSON API URL or None if not a supported URL
    """
    parsed = urlparse(url)
    
    # Remove trailing slash if present
    path = parsed.path.rstrip('/')
    
    # Swift.org documentation
    if parsed.netloc == 'www.swift.org' and '/documentation/' in path:
        # Replace /documentation/ with /data/documentation/ and add .json
        json_path = path.replace('/documentation/', '/data/documentation/') + '.json'
        json_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            json_path,
            '',
            '',
            ''
        ))
        return json_url
    
    # Apple Developer documentation
    elif parsed.netloc == 'developer.apple.com' and path.startswith('/documentation/'):
        # Extract the path after /documentation/
        doc_path = path[len('/documentation/'):]
        
        # Build the JSON URL
        json_path = f'/tutorials/data/documentation/{doc_path}.json'
        json_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            json_path,
            '',
            '',
            ''
        ))
        return json_url
    
    # Swift book documentation
    elif parsed.netloc == 'docs.swift.org' and '/documentation/' in path:
        # Replace /documentation/ with /data/documentation/ and add .json
        json_path = path.replace('/documentation/', '/data/documentation/') + '.json'
        json_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            json_path,
            '',
            '',
            ''
        ))
        return json_url
    
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python docc_url_converter.py <url>")
        print("\nExamples:")
        print("  Swift.org: https://www.swift.org/migration/documentation/migrationguide/")
        print("  Apple Dev: https://developer.apple.com/documentation/swift/updating_an_app_to_use_swift_concurrency")
        print("  Swift Book: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/")
        sys.exit(1)
    
    url = sys.argv[1]
    json_url = convert_docc_url_to_json(url)
    
    if json_url:
        print(json_url)
    else:
        print(f"Error: Not a valid DOCC documentation URL: {url}", file=sys.stderr)
        print("Supported domains: www.swift.org, developer.apple.com, docs.swift.org", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()