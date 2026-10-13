"""
ugit/data.py — The Core Storage Engine
=======================================
This module is the heart of K-Git. It handles all filesystem interactions:
  - Initializing the .kgit repository structure
  - Hashing file contents with SHA-1 (content-addressable storage)
  - Compressing/decompressing objects with zlib
  - Reading and writing all objects in the .kgit/objects store
  - Managing refs (branches, HEAD pointers)

KEY CONCEPT: Content-Addressable Storage
-----------------------------------------
Every piece of data stored in K-Git is identified by the SHA-1 hash of its
content. This means:
  1. The same content always produces the same hash (deterministic)
  2. Even a 1-byte change produces a completely different hash (avalanche effect)
  3. We can verify data integrity just by re-hashing it

OBJECT FORMAT (matches Git's format):
  "<type>\x00<raw_content>"
  e.g., "blob\x00Hello, World!\n"

This is then compressed with zlib and saved to .kgit/objects/<sha1_hash>
"""

import hashlib
import zlib
import os

# The root directory for all K-Git data. Officially customized from .ugit to .kgit!
GIT_DIR = ".kgit"


def init():
    """
    Initialize a new K-Git repository.

    Creates the hidden .kgit directory and the objects subdirectory.
    The objects directory is our "database" — every version of every file
    ever tracked will live here as a compressed, hashed object.

    Directory layout after init:
        .kgit/
        ├── objects/    ← content-addressable object store (blobs, trees, commits)
        └── HEAD        ← pointer to the current commit (created on first commit)
    """
    os.makedirs(GIT_DIR, exist_ok=True)
    os.makedirs(os.path.join(GIT_DIR, "objects"), exist_ok=True)
    print(f"Initialized empty K-Git repository in {os.path.abspath(GIT_DIR)}")


def hash_object(data: bytes, obj_type: str = "blob") -> str:
    """
    Store a byte string as an object in the K-Git object store.

    This is the fundamental write operation. It:
      1. Prepends a type header: "<type>\x00" (e.g., "blob\x00")
      2. Computes the SHA-1 hash of the full content (header + data)
      3. Compresses the full content with zlib (level 9 = max compression)
      4. Saves the compressed bytes to .kgit/objects/<sha1>
      5. Returns the 40-character hex SHA-1 string

    Args:
        data:     Raw bytes of the content to store (e.g., file contents).
        obj_type: The object type string. One of:
                    "blob"   → a file's raw contents
                    "tree"   → a directory listing (snapshot of a folder)
                    "commit" → a commit object (metadata + tree pointer)

    Returns:
        A 40-character lowercase hex string (the SHA-1 hash).
        This hash is the permanent "address" of this content.
    """
    # Step 1: Build the full object content: header + null byte + raw data
    header = f"{obj_type}\x00".encode()
    full_content = header + data

    # Step 2: SHA-1 hash the full content to get a unique 40-char hex string.
    sha1 = hashlib.sha1(full_content).hexdigest()

    # Step 3: Compress the full content with zlib at max compression.
    compressed = zlib.compress(full_content, level=9)

    # Step 4: Write to the object store. The path is simply .kgit/objects/<sha1>.
    obj_path = os.path.join(GIT_DIR, "objects", sha1)
    with open(obj_path, "wb") as f:
        f.write(compressed)

    return sha1


def get_object(sha1: str, expected_type: str = None) -> bytes:
    """
    Retrieve and decompress a raw object from the object store.

    This is the fundamental read operation, the inverse of hash_object().
    It:
      1. Reads the compressed file from .kgit/objects/<sha1>
      2. Decompresses it with zlib
      3. Strips the "<type>\x00" header
      4. Optionally validates the object type
      5. Returns the raw data bytes
    """
    obj_path = os.path.join(GIT_DIR, "objects", sha1)

    with open(obj_path, "rb") as f:
        compressed = f.read()

    # Decompress to get back the full content: "<type>\x00<raw_data>"
    full_content = zlib.decompress(compressed)

    # Split on the null byte to separate the header from the actual data.
    null_index = full_content.index(b"\x00")
    obj_type = full_content[:null_index].decode()
    raw_data = full_content[null_index + 1:]

    # Type validation: catch programmer errors early and loudly.
    if expected_type is not None and obj_type != expected_type:
        raise ValueError(
            f"Object type mismatch: expected '{expected_type}', "
            f"but found '{obj_type}' for object {sha1}"
        )

    return raw_data


# ---------------------------------------------------------------------------
# REF MANAGEMENT
# Refs are named pointers to commit hashes. Examples:
#   HEAD            → the currently checked-out commit
#   refs/heads/main → the tip of the "main" branch
# They are stored as plain text files containing a 40-char SHA-1.
# ---------------------------------------------------------------------------

def update_ref(ref: str, sha1: str):
    """
    Create or update a named reference (a named pointer to a commit hash).

    Args:
        ref:  Relative path inside .kgit/, e.g. "HEAD" or "refs/heads/main"
        sha1: The 40-character commit hash to point this ref at.
    """
    ref_path = os.path.join(GIT_DIR, ref)
    # Ensure the parent directory exists (e.g., .kgit/refs/heads/)
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, "w") as f:
        f.write(sha1)


def get_ref(ref: str) -> str | None:
    """
    Read the commit hash stored in a named reference file.

    Args:
        ref: Relative path inside .kgit/, e.g. "HEAD"

    Returns:
        The 40-character SHA-1 string, or None if the ref doesn't exist yet.
    """
    ref_path = os.path.join(GIT_DIR, ref)
    if not os.path.isfile(ref_path):
        return None
    with open(ref_path, "r") as f:
        return f.read().strip()