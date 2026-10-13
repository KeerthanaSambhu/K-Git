# K-Git: Distributed Version Control Engine & Dashboard

A lightweight, fully functional version control system built from scratch in Python, complete with a FastAPI service layer and a React visualization dashboard.

---

## ⚡ Core Architecture

K-Git mirrors Git's low-level content-addressable storage model:

- **Content-Addressable Storage:** Files and directories are indexed by cryptographic SHA-1 hashes of their content.
- **Binary Compression:** Object payloads (blobs, trees, commits) are compressed using standard `zlib` (Level 9).
- **Directed Acyclic Graph (DAG):** Commits link backwards to their parent commit hashes, forming a verifiable historical timeline.
- **Tree Structures:** Recursive directory traversal storing mode, file type, SHA-1 fingerprint, and relative paths.

---

## 🛠️ Project Structure

```text
K-Git/
├── ugit/               # Core Python VCS engine
│   ├── cli.py          # Command-line interface & argument parser
│   └── data.py         # Low-level I/O, hashing, and ref management
├── api.py              # FastAPI REST backend wrapper
├── frontend/           # Vite + React visual control dashboard
├── ugit.py             # Primary CLI executable entry point
└── .gitignore          # Repository ignore rules