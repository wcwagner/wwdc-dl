#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Add FrontMatter to all markdown files in the sources directory.
"""

import os
import yaml
from datetime import datetime
from pathlib import Path

def get_title_from_content(content):
    """Extract title from first heading in markdown."""
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled"

def determine_type(file_path):
    """Determine content type based on path."""
    if 'swift-org' in file_path:
        return 'tutorial'
    elif 'apple-dev' in file_path:
        return 'reference'
    elif 'blogs' in file_path:
        return 'article'
    elif 'github' in file_path:
        return 'repository'
    elif 'wwdc' in file_path:
        return 'transcript'
    return 'article'

def determine_topics(file_path, content):
    """Determine topics based on content and path."""
    topics = ['swift6', 'concurrency']
    
    content_lower = content.lower()
    if 'migration' in content_lower or 'migrating' in content_lower:
        topics.append('migration')
    if 'actor' in content_lower:
        topics.append('actors')
    if 'sendable' in content_lower:
        topics.append('sendable')
    if 'task' in content_lower:
        topics.append('tasks')
    if 'async' in content_lower or 'await' in content_lower:
        topics.append('async-await')
    if 'data race' in content_lower or 'data-race' in content_lower:
        topics.append('data-race-safety')
    
    return sorted(list(set(topics)))

def add_frontmatter(file_path):
    """Add FrontMatter to a markdown file if it doesn't already have it."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has FrontMatter
    if content.startswith('---\n'):
        print(f"Skipping {file_path} - already has FrontMatter")
        return
    
    # Extract title and prepare FrontMatter
    title = get_title_from_content(content)
    
    # Try to find source URL from crawled-urls.md
    source_url = None
    crawled_urls_path = Path(__file__).parent / 'crawled-urls.md'
    if crawled_urls_path.exists():
        with open(crawled_urls_path, 'r') as f:
            crawled_content = f.read()
            file_name = os.path.basename(file_path)
            for line in crawled_content.split('\n'):
                if file_name in line and '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        url = parts[1].strip()
                        if url.startswith('http'):
                            source_url = url
                            break
    
    frontmatter = {
        'title': title,
        'source': source_url or 'Unknown',
        'date_crawled': datetime.now().strftime('%Y-%m-%d'),
        'type': determine_type(str(file_path)),
        'topics': determine_topics(str(file_path), content)
    }
    
    # Create FrontMatter YAML
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    
    # Add FrontMatter to content
    new_content = f"---\n{yaml_content}---\n\n{content}"
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Added FrontMatter to {file_path}")

def main():
    """Process all markdown files in sources directory."""
    sources_dir = Path(__file__).parent / 'sources'
    
    for md_file in sources_dir.rglob('*.md'):
        add_frontmatter(md_file)

if __name__ == '__main__':
    main()