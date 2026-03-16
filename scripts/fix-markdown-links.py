#!/usr/bin/env python3
"""
Script to fix markdown hyperlinking errors throughout the repository.
Converts backtick file references like `docs/FILE.md` to proper markdown links [docs/FILE.md](docs/FILE.md).
"""

import os
import re
import sys
from pathlib import Path

def fix_markdown_links(file_path):
    """Fix markdown hyperlinking errors in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match backtick-enclosed .md files that are likely file references
        # More specific pattern to avoid inline code
        pattern = r'`([a-zA-Z0-9_/-]+\.md)`'
        
        # Apply the replacement
        content = re.sub(pattern, r'[\1](\1)', content)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all markdown files."""
    repo_root = Path(__file__).parent
    fixed_files = []
    error_files = []
    
    # Find all markdown files, excluding node_modules
    for md_file in repo_root.rglob("*.md"):
        if "node_modules" in str(md_file):
            continue
            
        if fix_markdown_links(md_file):
            fixed_files.append(str(md_file))
            print(f"Fixed: {md_file}")
    
    print(f"\nSummary:")
    print(f"Files fixed: {len(fixed_files)}")
    print(f"Files with errors: {len(error_files)}")
    
    if fixed_files:
        print(f"\nFixed files:")
        for file in sorted(fixed_files):
            print(f"  - {file}")
    
    if error_files:
        print(f"\nFiles with errors:")
        for file in sorted(error_files):
            print(f"  - {file}")

if __name__ == "__main__":
    main()
