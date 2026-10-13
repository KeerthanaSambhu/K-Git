"""
ugit/cli.py — Command-Line Interface & Command Implementations
==============================================================
This module handles two responsibilities:
  1. ARGUMENT PARSING: Defines all K-Git subcommands using argparse.
     Each subcommand maps to a Python function.
  2. COMMAND LOGIC: Implements the high-level logic for each command.
     Commands in this file call into data.py for all storage operations.

PHASE 1 COMMANDS:
  init         → Set up a new repository
  hash-object  → Store a file as a blob object, print its SHA-1
  cat-file     → Retrieve and print an object's raw contents

PHASE 2 COMMANDS:
  write-tree   → Snapshot the current directory into a tree object
  read-tree    → Restore a directory structure from a tree hash

PHASE 3 COMMANDS:
  commit       → Record a snapshot with a message and parent pointer
  log          → Walk the commit history and display it
  checkout     → Restore the working directory to a past commit

CUSTOM COMMANDS:
  status-report → Displays a formatted engineering metrics dashboard
"""

import argparse
import os
import sys
import time

from ugit import data


# ===========================================================================
# ARGUMENT PARSER SETUP
# ===========================================================================

def create_parser() -> argparse.ArgumentParser:
    """
    Build and return the top-level argument parser with all subcommands.

    Using argparse gives us:
      - Automatic --help documentation
      - Type checking on arguments
      - Clean error messages for bad input
    """
    parser = argparse.ArgumentParser(
        prog="kgit",
        description="K-Git: Keerthana's Custom Version Control System Built from Scratch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kgit init
  kgit hash-object myfile.txt
  kgit cat-file <sha1>
  kgit write-tree
  kgit read-tree <sha1>
  kgit commit -m "Initial commit"
  kgit log
  kgit checkout <sha1>
  kgit status-report
        """
    )

    # The subparsers object lets us define subcommands like: kgit <subcommand> [args]
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True  # Show error if no subcommand is given

    # -----------------------------------------------------------------------
    # PHASE 1 SUBCOMMANDS
    # -----------------------------------------------------------------------

    # 'init' — no arguments needed
    subparsers.add_parser(
        "init",
        help="Initialize a new K-Git repository in the current directory"
    )

    # 'hash-object <file>' — takes a filename to hash
    hash_parser = subparsers.add_parser(
        "hash-object",
        help="Compute SHA-1 hash of a file, store it as a blob, and print the hash"
    )
    hash_parser.add_argument(
        "file",
        metavar="<file>",
        help="Path to the file to hash and store"
    )

    # 'cat-file <object>' — takes a sha1 hash
    cat_parser = subparsers.add_parser(
        "cat-file",
        help="Print the decompressed contents of a stored object"
    )
    cat_parser.add_argument(
        "object",
        metavar="<sha1>",
        help="The 40-character SHA-1 hash of the object to retrieve"
    )

    # -----------------------------------------------------------------------
    # PHASE 2 SUBCOMMANDS
    # -----------------------------------------------------------------------

    # 'write-tree' — no arguments; always snapshots current directory
    subparsers.add_parser(
        "write-tree",
        help="Recursively snapshot the current directory into a tree object"
    )

    # 'read-tree <tree>' — takes the tree sha1 to restore
    read_tree_parser = subparsers.add_parser(
        "read-tree",
        help="Restore a directory structure from a tree object hash"
    )
    read_tree_parser.add_argument(
        "tree",
        metavar="<sha1>",
        help="The SHA-1 hash of the tree object to restore"
    )

    # -----------------------------------------------------------------------
    # PHASE 3 SUBCOMMANDS
    # -----------------------------------------------------------------------

    # 'commit -m <message>'
    commit_parser = subparsers.add_parser(
        "commit",
        help="Record the current state as a new commit"
    )
    commit_parser.add_argument(
        "-m", "--message",
        required=True,
        metavar="<message>",
        help="The commit message describing this snapshot"
    )

    # 'log' — no arguments; always walks from HEAD
    subparsers.add_parser(
        "log",
        help="Show the commit history starting from HEAD"
    )

    # 'checkout <commit>'
    checkout_parser = subparsers.add_parser(
        "checkout",
        help="Restore the working directory to the state of a given commit"
    )
    checkout_parser.add_argument(
        "commit",
        metavar="<sha1>",
        help="The SHA-1 hash of the commit to check out"
    )

    # -----------------------------------------------------------------------
    # CUSTOM SUBCOMMANDS
    # -----------------------------------------------------------------------
    subparsers.add_parser(
        "status-report",
        help="Displays a formatted engineering metrics report of your local database"
    )

    return parser


# ===========================================================================
# COMMAND IMPLEMENTATIONS — PHASE 1
# ===========================================================================

def cmd_init(args):
    """
    'kgit init'

    Initialize a new K-Git repository in the current working directory.
    Creates .ugit/ and .ugit/objects/.
    Safe to call on an existing repo (won't overwrite existing data).
    """
    data.init()


def cmd_hash_object(args):
    """
    'kgit hash-object <file>'

    Read a file's contents, store it as a blob object, and print its SHA-1.
    """
    with open(args.file, "rb") as f:
        file_data = f.read()

    sha1 = data.hash_object(file_data, obj_type="blob")
    print(sha1)


def cmd_cat_file(args):
    """
    'kgit cat-file <sha1>'

    Retrieve a stored object by its SHA-1 hash and print its raw contents.
    """
    raw_data = data.get_object(args.object)
    sys.stdout.buffer.write(raw_data)


# ===========================================================================
# COMMAND IMPLEMENTATIONS — PHASE 2
# ===========================================================================

def cmd_write_tree(args):
    """
    'kgit write-tree'

    Recursively snapshot the entire current directory into the object store,
    and print the SHA-1 of the root tree object.
    """
    root_sha1 = _write_tree_recursive(".")
    print(root_sha1)


def _write_tree_recursive(directory: str) -> str:
    """
    Internal helper: recursively build tree objects for a directory.
    """
    # Directories we never want to include in a snapshot
    # Adding .kgit to the set to make it future-proof for database renames
    IGNORED_DIRS = {".ugit", ".kgit", "__pycache__", ".git", "node_modules", ".DS_Store"}

    entries = []  # Will hold (type, sha1, name) tuples

    try:
        dir_entries = sorted(os.listdir(directory))  # Sorted for deterministic hashes
    except PermissionError:
        return None

    for name in dir_entries:
        if name in IGNORED_DIRS:
            continue

        full_path = os.path.join(directory, name)

        if os.path.isfile(full_path):
            with open(full_path, "rb") as f:
                file_data = f.read()
            sha1 = data.hash_object(file_data, obj_type="blob")
            entries.append(("blob", sha1, name))

        elif os.path.isdir(full_path):
            tree_sha1 = _write_tree_recursive(full_path)
            if tree_sha1 is not None:
                entries.append(("tree", tree_sha1, name))

    tree_content = "\n".join(
        f"{entry_type} {sha1} {name}"
        for entry_type, sha1, name in entries
    ).encode()

    return data.hash_object(tree_content, obj_type="tree")


def cmd_read_tree(args):
    """
    'kgit read-tree <sha1>'

    Restore a directory structure from a tree object onto the filesystem.
    """
    _read_tree_recursive(args.tree, base_path=".")
    print(f"Restored tree {args.tree[:8]}... to working directory.")


def _read_tree_recursive(tree_sha1: str, base_path: str):
    """
    Internal helper: recursively restore a tree object to the filesystem.
    """
    raw_tree = data.get_object(tree_sha1, expected_type="tree")
    tree_content = raw_tree.decode()

    if not tree_content.strip():
        return  # Empty directory — nothing to restore

    for line in tree_content.splitlines():
        parts = line.strip().split(" ", 2)
        if len(parts) != 3:
            continue

        entry_type, entry_sha1, entry_name = parts
        entry_path = os.path.join(base_path, entry_name)

        if entry_type == "blob":
            blob_data = data.get_object(entry_sha1, expected_type="blob")
            os.makedirs(os.path.dirname(entry_path), exist_ok=True)
            with open(entry_path, "wb") as f:
                f.write(blob_data)

        elif entry_type == "tree":
            os.makedirs(entry_path, exist_ok=True)
            _read_tree_recursive(entry_sha1, base_path=entry_path)


# ===========================================================================
# COMMAND IMPLEMENTATIONS — PHASE 3
# ===========================================================================

def cmd_commit(args):
    """
    'kgit commit -m <message>'

    Record the current state of the working directory as a permanent snapshot.
    """
    tree_sha1 = _write_tree_recursive(".")

    lines = []
    lines.append(f"tree {tree_sha1}")

    parent_sha1 = data.get_ref("HEAD")
    if parent_sha1:
        lines.append(f"parent {parent_sha1}")

    lines.append(f"author K-Git User")
    lines.append(f"timestamp {int(time.time())}")
    lines.append(f"")  # Blank line separating metadata from message
    lines.append(args.message)

    commit_content = "\n".join(lines).encode()
    commit_sha1 = data.hash_object(commit_content, obj_type="commit")
    data.update_ref("HEAD", commit_sha1)

    print(f"[K-Git] Committed: {commit_sha1[:8]}...  \"{args.message}\"")
    return commit_sha1


def cmd_log(args):
    """
    'kgit log'

    Walk the commit history backwards from HEAD and display each commit.
    """
    current_sha1 = data.get_ref("HEAD")

    if current_sha1 is None:
        print("No commits yet. Make your first commit with: kgit commit -m 'message'")
        return

    visited = set()
    while current_sha1 and current_sha1 not in visited:
        visited.add(current_sha1)

        raw_commit = data.get_object(current_sha1, expected_type="commit")
        commit_text = raw_commit.decode()

        fields = {}
        lines = commit_text.splitlines()
        message_lines = []
        in_message = False

        for line in lines:
            if in_message:
                message_lines.append(line)
            elif line == "":
                in_message = True
            else:
                key, _, value = line.partition(" ")
                fields[key] = value.strip()

        message = "\n".join(message_lines).strip()
        timestamp = int(fields.get("timestamp", 0))
        readable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        print(f"\033[33mcommit {current_sha1}\033[0m")  # Yellow hash
        print(f"Date:   {readable_time}")
        print(f"\n    {message}\n")

        current_sha1 = fields.get("parent")


def cmd_checkout(args):
    """
    'kgit checkout <sha1>'

    Restore the entire working directory to the exact state of a given commit.
    """
    commit_sha1 = args.commit

    raw_commit = data.get_object(commit_sha1, expected_type="commit")
    commit_text = raw_commit.decode()

    tree_sha1 = None
    for line in commit_text.splitlines():
        if line.startswith("tree "):
            tree_sha1 = line.split(" ", 1)[1].strip()
            break

    if tree_sha1 is None:
        print(f"Error: Commit {commit_sha1[:8]} has no tree reference.")
        sys.exit(1)

    _clear_working_directory(".")
    _read_tree_recursive(tree_sha1, base_path=".")
    data.update_ref("HEAD", commit_sha1)

    print(f"[K-Git] HEAD is now at {commit_sha1[:8]}...")


def _clear_working_directory(directory: str):
    """
    Remove all files and directories in `directory`, keeping databases safe.
    """
    PROTECTED = {".ugit", ".kgit", ".git"}  # Keep database files safe

    for name in os.listdir(directory):
        if name in PROTECTED:
            continue

        full_path = os.path.join(directory, name)

        if os.path.isfile(full_path) or os.path.islink(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            import shutil
            shutil.rmtree(full_path)


# ===========================================================================
# CUSTOM METRICS DASHBOARD IMPLEMENTATION
# ===========================================================================

def cmd_status_report(args):
    """
    'kgit status-report'
    
    Reads the active hidden database directly, calculates metadata metrics, 
    and outputs a polished terminal-ready engine report status.
    """
    # Auto-detect whichever database path folder is configured in data.py
    db_folder = getattr(data, 'GIT_DIR', '.ugit') 
    path = os.path.join(db_folder, 'objects')
    
    if not os.path.exists(path):
        print(f"\033[31m[Error]\033[0m No repository found. Run 'python ugit.py init' first!")
        return
    
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    
    print("\033[36m" + "=" * 55 + "\033[0m")
    print(f"   📊 \033[1mK-GIT CORE ENGINE: SYSTEM STATUS REPORT\033[0m")
    print("\033[36m" + "=" * 55 + "\033[0m")
    print(f" • Database Status   ➔ \033[32mActive\033[0m")
    print(f" • Engine Location   ➔ {os.path.abspath(db_folder)}")
    print(f" • Total Unique Blobs➔ \033[1m{len(files)}\033[0m compressed objects tracked")
    print("\033[36m" + "-" * 55 + "\033[0m")
    
    if files:
        print(" Registered Content Fingerprints (First 10 Characters):")
        for i, f in enumerate(files, 1):
            print(f"   [{i:02d}] ➔ \033[33m{f[:10]}\033[0m...")
    else:
        print(" No objects tracked yet. Use 'hash-object' or 'commit' to store data.")
    print("\033[36m" + "=" * 55 + "\033[0m")


# ===========================================================================
# MAIN DISPATCH FUNCTION
# ===========================================================================

def main():
    """
    Entry point: parse arguments and dispatch to the correct command function.
    """
    parser = create_parser()
    args = parser.parse_args()

    command_map = {
        "init":          cmd_init,
        "hash-object":   cmd_hash_object,
        "cat-file":      cmd_cat_file,
        "write-tree":    cmd_write_tree,
        "read-tree":     cmd_read_tree,
        "commit":        cmd_commit,
        "log":           cmd_log,
        "checkout":      cmd_checkout,
        "status-report": cmd_status_report,
    }

    handler = command_map.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)