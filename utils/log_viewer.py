#!/usr/bin/env python3
"""
Log Viewer Utility for Hyland Hockey Jersey Order Management System

This utility provides a simple way to view and filter log files.
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


class LogViewer:
    """Simple log file viewer with filtering capabilities."""
    
    def __init__(self, log_dir: str = "logs", quiet: bool = False):
        """
        Initialize the log viewer.
        
        Args:
            log_dir: Directory containing log files
            quiet: If True, suppress all output (for use in GUI)
        """
        self.log_dir = Path(log_dir)
        self.quiet = quiet
        if not self.log_dir.exists():
            if not self.quiet:
                print(f"Log directory not found: {self.log_dir}")
            sys.exit(1)
    
    def list_log_files(self) -> List[Path]:
        """List all available log files."""
        log_files = list(self.log_dir.glob("*.log"))
        return sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def display_log_files(self):
        """Display all available log files with their sizes and modification times."""
        log_files = self.list_log_files()
        
        if not log_files:
            if not self.quiet:
                print("No log files found.")
            return
        
        if not self.quiet:
            print(f"\nAvailable log files in {self.log_dir}:")
            print("-" * 80)
            print(f"{'Filename':<30} {'Size':<10} {'Modified':<20} {'Lines':<8}")
            print("-" * 80)
        
        for log_file in log_files:
            stat = log_file.stat()
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            # Count lines
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
            except Exception:
                line_count = "Error"
            
            # Format size
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024 * 1024:
                size_str = f"{size // 1024}KB"
            else:
                size_str = f"{size // (1024 * 1024)}MB"
            
            if not self.quiet:
                print(f"{log_file.name:<30} {size_str:<10} {modified:<20} {line_count:<8}")
    
    def view_log(self, filename: str, lines: int = 50, level: Optional[str] = None, 
                 search: Optional[str] = None, since: Optional[str] = None):
        """
        View a specific log file with optional filtering.
        
        Args:
            filename: Name of the log file to view
            lines: Number of lines to show (0 for all)
            level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            search: Search for specific text
            since: Show logs since this time (format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
        """
        log_file = self.log_dir / filename
        
        if not log_file.exists():
            if not self.quiet:
                print(f"Log file not found: {log_file}")
            return
        
        # Parse since time
        since_time = None
        if since:
            try:
                if len(since) == 10:  # YYYY-MM-DD
                    since_time = datetime.strptime(since, "%Y-%m-%d")
                else:  # YYYY-MM-DD HH:MM:SS
                    since_time = datetime.strptime(since, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                if not self.quiet:
                    print(f"Invalid date format: {since}. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")
                return
        
        if not self.quiet:
            print(f"\nViewing log file: {log_file}")
            print(f"Filters: lines={lines if lines > 0 else 'all'}, level={level or 'all'}, "
                  f"search='{search or 'none'}', since={since or 'none'}")
            print("-" * 80)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
                # Apply filters
                filtered_lines = []
                for line in all_lines:
                    # Check since filter
                    if since_time:
                        try:
                            # Extract timestamp from log line (assuming format: YYYY-MM-DD HH:MM:SS)
                            timestamp_str = line[:19]  # First 19 characters
                            line_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if line_time < since_time:
                                continue
                        except (ValueError, IndexError):
                            # Skip lines that don't have proper timestamps
                            continue
                    
                    # Check level filter
                    if level and level.upper() not in line.upper():
                        continue
                    
                    # Check search filter
                    if search and search.lower() not in line.lower():
                        continue
                    
                    filtered_lines.append(line)
                
                # Apply line limit
                if lines > 0:
                    filtered_lines = filtered_lines[-lines:]
                
                # Display results
                if not filtered_lines:
                    if not self.quiet:
                        print("No log entries match the specified filters.")
                else:
                    for line in filtered_lines:
                        if not self.quiet:
                            print(line.rstrip())
                    
                    if not self.quiet:
                        print(f"\n--- End of log (showing {len(filtered_lines)} of {len(all_lines)} lines) ---")
                    
        except Exception as e:
            if not self.quiet:
                print(f"Error reading log file: {e}")
    
    def tail_log(self, filename: str, lines: int = 20, follow: bool = False):
        """
        Tail a log file (show last N lines and optionally follow).
        
        Args:
            filename: Name of the log file to tail
            lines: Number of lines to show
            follow: Whether to follow the log file (not implemented yet)
        """
        log_file = self.log_dir / filename
        
        if not log_file.exists():
            if not self.quiet:
                print(f"Log file not found: {log_file}")
            return
        
        if not self.quiet:
            print(f"\nTailing log file: {log_file} (last {lines} lines)")
            print("-" * 80)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in last_lines:
                    if not self.quiet:
                        print(line.rstrip())
                
                if follow and not self.quiet:
                    print("\nFollow mode not yet implemented. Use 'tail -f' command instead.")
                    
        except Exception as e:
            if not self.quiet:
                print(f"Error reading log file: {e}")


def main():
    """Main entry point for the log viewer."""
    parser = argparse.ArgumentParser(description="Log Viewer for Hyland Hockey Jersey Order Management System")
    parser.add_argument("--log-dir", default="logs", help="Log directory (default: logs)")
    parser.add_argument("--list", action="store_true", help="List available log files")
    parser.add_argument("--file", help="Log file to view")
    parser.add_argument("--lines", type=int, default=50, help="Number of lines to show (default: 50, 0 for all)")
    parser.add_argument("--level", help="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    parser.add_argument("--search", help="Search for specific text")
    parser.add_argument("--since", help="Show logs since this time (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--tail", type=int, help="Show last N lines (like tail command)")
    parser.add_argument("--follow", action="store_true", help="Follow log file (with --tail)")
    
    args = parser.parse_args()
    
    viewer = LogViewer(args.log_dir)
    
    if args.list:
        viewer.display_log_files()
    elif args.file:
        if args.tail:
            viewer.tail_log(args.file, args.tail, args.follow)
        else:
            viewer.view_log(args.file, args.lines, args.level, args.search, args.since)
    else:
        # Default: list log files
        viewer.display_log_files()


if __name__ == "__main__":
    main() 