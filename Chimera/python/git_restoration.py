"""
Git-Based Deleted Files Restoration Utility

Provides functionality to restore deleted or modified files using git history.
Supports both file restoration and directory restoration from previous commits.
"""

import argparse
import subprocess
from pathlib import Path
from typing import Optional


def get_git_root() -> Optional[Path]:
    """Get the root directory of the git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


def restore_deleted_file(file_path: str, commit_ref: str = "HEAD") -> bool:
    """Restore a deleted or modified file from git history.
    
    Args:
        file_path: Relative path to the file from the git root
        commit_ref: Git reference (commit hash, branch name, or 'HEAD')
        
    Returns:
        True if restoration was successful, False otherwise
    """
    git_root = get_git_root()
    if not git_root:
        raise RuntimeError("Not a git repository or unable to determine git root")

    full_path = git_root / file_path
    
    # Check if file exists in the specified commit
    try:
        subprocess.run(
            ["git", "show", f"{commit_ref}:{file_path}"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        raise ValueError(f"File {file_path} not found in git history at {commit_ref}")

    # Restore the file from git history
    try:
        subprocess.run(
            ["git", "checkout", commit_ref, "--", file_path],
            capture_output=True,
            check=True
        )
        print(f"Successfully restored {file_path} from {commit_ref}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to restore {file_path}: {e}")
        return False


def restore_files_by_pattern(pattern: str, commit_ref: str = "HEAD") -> list[str]:
    """Restore all files matching a pattern from git history.
    
    Args:
        pattern: File pattern (e.g., '*.py', 'Chimera/Python/*.py')
        commit_ref: Git reference
        
    Returns:
        List of successfully restored file paths
    """
    git_root = get_git_root()
    if not git_root:
        raise RuntimeError("Not a git repository or unable to determine git root")

    # Find files matching the pattern in git history
    try:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit_ref, "--", pattern],
            capture_output=True,
            text=True,
            check=True
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except subprocess.CalledProcessError:
        raise ValueError(f"No files found matching pattern {pattern} at {commit_ref}")

    restored_files = []
    for file_path in files:
        if restore_deleted_file(file_path, commit_ref):
            restored_files.append(file_path)

    return restored_files


def get_deleted_files_since_commit(commit_ref: str = "HEAD") -> list[str]:
    """Get a list of files that have been deleted since the specified commit.
    
    Args:
        commit_ref: Git reference
        
    Returns:
        List of deleted file paths
    """
    git_root = get_git_root()
    if not git_root:
        raise RuntimeError("Not a git repository or unable to determine git root")

    try:
        # Get list of deleted files between previous commit and HEAD
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{commit_ref}^", commit_ref, "--diff-filter=D"],
            capture_output=True,
            text=True,
            check=True
        )
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except subprocess.CalledProcessError:
        return []


def unstage_and_restore_all() -> bool:
    """Unstage all changes and restore all files to the state of HEAD.
    
    Returns:
        True if successful, False otherwise
    """
    git_root = get_git_root()
    if not git_root:
        raise RuntimeError("Not a git repository or unable to determine git root")

    try:
        # Unstage all changes
        subprocess.run(
            ["git", "reset"],
            capture_output=True,
            check=True
        )
        # Restore all files
        subprocess.run(
            ["git", "restore", "."],
            capture_output=True,
            check=True
        )
        print("Successfully unstaged and restored all files")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to unstage and restore files: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Git-Based Deleted Files Restoration Utility")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Restore specific file command
    restore_parser = subparsers.add_parser("restore-file", help="Restore a specific deleted file")
    restore_parser.add_argument("file_path", help="Relative path to the file from the git root")
    restore_parser.add_argument("--commit-ref", default="HEAD", help="Git reference (default: HEAD)")
    
    # Restore files by pattern command
    pattern_parser = subparsers.add_parser("restore-pattern", help="Restore all files matching a pattern")
    pattern_parser.add_argument("pattern", help="File pattern (e.g., '*.py', 'Chimera/Python/*.py')")
    pattern_parser.add_argument("--commit-ref", default="HEAD", help="Git reference (default: HEAD)")
    
    # List deleted files command
    list_deleted_parser = subparsers.add_parser("list-deleted-since", help="List deleted files since a commit")
    list_deleted_parser.add_argument("--commit-ref", default="HEAD", help="Git reference (default: HEAD)")
    
    # Restore all command
    restore_all_parser = subparsers.add_parser("restore-all", help="Unstage and restore all changes to HEAD state")

    args = parser.parse_args()

    if args.command == "restore-file":
        try:
            success = restore_deleted_file(args.file_path, args.commit_ref)
            if not success:
                print(f"Failed to restore {args.file_path}")
                return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1
            
    elif args.command == "restore-pattern":
        try:
            restored_files = restore_files_by_pattern(args.pattern, args.commit_ref)
            print(f"Restored {len(restored_files)} files matching pattern '{args.pattern}':")
            for f in restored_files:
                print(f"  - {f}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
            
    elif args.command == "list-deleted-since":
        try:
            deleted_files = get_deleted_files_since_commit(args.commit_ref)
            if not deleted_files:
                print(f"No deleted files found since {args.commit_ref}")
            else:
                print(f"Deleted files since {args.commit_ref}:")
                for f in deleted_files:
                    print(f"  - {f}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
            
    elif args.command == "restore-all":
        try:
            success = unstage_and_restore_all()
            if not success:
                print("Failed to unstaged and restore all files")
                return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1
            
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
