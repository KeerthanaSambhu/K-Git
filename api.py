"""
api.py — FastAPI REST Wrapper for K-Git
Exposes K-Git storage engine functions to HTTP clients.
"""

import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ugit import data
from ugit import cli

app = FastAPI(title="K-Git Engine API", version="1.0.0")

# Enable CORS for React frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CommitRequest(BaseModel):
    message: str


@app.get("/api/status")
def get_status():
    """Returns database operational status and stored object fingerprints."""
    db_folder = getattr(data, "GIT_DIR", ".kgit")
    objects_path = os.path.join(db_folder, "objects")

    if not os.path.exists(objects_path):
        return {
            "initialized": False,
            "status": "Not Initialized",
            "db_path": os.path.abspath(db_folder),
            "total_objects": 0,
            "fingerprints": [],
        }

    files = [
        f for f in os.listdir(objects_path)
        if os.path.isfile(os.path.join(objects_path, f))
    ]

    return {
        "initialized": True,
        "status": "Active",
        "db_path": os.path.abspath(db_folder),
        "total_objects": len(files),
        "fingerprints": [f[:10] for f in sorted(files)],
    }


@app.post("/api/init")
def init_repo():
    """Initializes the .kgit directory store."""
    data.init()
    return {"message": "Repository initialized successfully"}


@app.get("/api/log")
def get_log():
    """Walks the commit history from HEAD and returns nodes as JSON."""
    current_sha1 = data.get_ref("HEAD")
    if not current_sha1:
        return []

    commits = []
    visited = set()

    while current_sha1 and current_sha1 not in visited:
        visited.add(current_sha1)

        try:
            raw_commit = data.get_object(current_sha1, expected_type="commit")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read commit {current_sha1}: {str(e)}")

        commit_text = raw_commit.decode()
        fields = {}
        message_lines = []
        in_message = False

        for line in commit_text.splitlines():
            if in_message:
                message_lines.append(line)
            elif line == "":
                in_message = True
            else:
                key, _, value = line.partition(" ")
                fields[key] = value.strip()

        timestamp = int(fields.get("timestamp", 0))
        readable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        commits.append({
            "sha1": current_sha1,
            "tree": fields.get("tree"),
            "parent": fields.get("parent"),
            "author": fields.get("author", "Unknown"),
            "timestamp": timestamp,
            "date": readable_time,
            "message": "\n".join(message_lines).strip(),
            "is_head": len(commits) == 0,
        })

        current_sha1 = fields.get("parent")

    return commits


@app.post("/api/commit")
def create_commit(payload: CommitRequest):
    """Snapshots working directory and advances HEAD."""
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Commit message cannot be empty.")

    tree_sha1 = cli._write_tree_recursive(".")
    if not tree_sha1:
        raise HTTPException(status_code=500, detail="Failed to generate tree snapshot.")

    lines = [f"tree {tree_sha1}"]
    parent_sha1 = data.get_ref("HEAD")
    if parent_sha1:
        lines.append(f"parent {parent_sha1}")

    lines.append("author K-Git Web User")
    lines.append(f"timestamp {int(time.time())}")
    lines.append("")
    lines.append(payload.message.strip())

    commit_content = "\n".join(lines).encode()
    commit_sha1 = data.hash_object(commit_content, obj_type="commit")
    data.update_ref("HEAD", commit_sha1)

    return {
        "commit_sha1": commit_sha1,
        "tree_sha1": tree_sha1,
        "message": payload.message.strip(),
    }