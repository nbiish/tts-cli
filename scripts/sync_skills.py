#!/usr/bin/env python3
"""Cross-Repository Skill Distribution & Integrity Verification Tool.

Ensures that the authoritative `tts-cli` skill file (.agents/skills/tts-cli/SKILL.md)
is synchronized byte-identically across consuming repositories with cryptographic
SHA-256 digest verification.
"""

import argparse
import hashlib
import sys
from pathlib import Path
from typing import List, Tuple, Optional


def find_repo_root() -> Path:
    """Find the root directory of the tts-cli repository."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".agents" / "skills" / "tts-cli" / "SKILL.md").is_file():
            return current
        if (current / "tts_cli").is_dir() and (current / "setup.py").is_file():
            return current
        current = current.parent
    # Fallback to current working directory
    return Path.cwd()


def get_source_skill_path(repo_root: Optional[Path] = None) -> Path:
    """Get the authoritative tts-cli SKILL.md path."""
    root = repo_root or find_repo_root()
    return root / ".agents" / "skills" / "tts-cli" / "SKILL.md"


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def discover_default_targets(repo_root: Optional[Path] = None) -> List[Path]:
    """Discover known consuming repositories for tts-cli skill synchronization."""
    root = repo_root or find_repo_root()
    candidates = [
        root.parent / "ainish-coder" / ".agents" / "skills" / "tts-cli" / "SKILL.md",
        Path.home() / "code" / "ainish-coder" / ".agents" / "skills" / "tts-cli" / "SKILL.md",
        Path.home() / ".config" / "ainish-coder" / ".agents" / "skills" / "tts-cli" / "SKILL.md",
    ]
    
    seen = set()
    valid_targets = []
    for candidate in candidates:
        resolved = candidate.resolve()
        # Check if parent repo exists
        if resolved.parent.parent.parent.is_dir() and resolved not in seen:
            seen.add(resolved)
            valid_targets.append(resolved)
            
    return valid_targets


def check_skill_sync(
    source_path: Path,
    targets: List[Path],
) -> Tuple[bool, List[Tuple[Path, str, bool]]]:
    """Check if all targets match the source SKILL.md byte-for-byte.

    Returns:
        (all_synced, list_of_(target_path, target_sha256_or_status, is_identical))
    """
    if not source_path.is_file():
        raise FileNotFoundError(f"Authoritative source skill not found at: {source_path}")

    source_sha = compute_sha256(source_path)
    source_bytes = source_path.read_bytes()

    results = []
    all_in_sync = True

    for target in targets:
        if not target.is_file():
            results.append((target, "MISSING", False))
            all_in_sync = False
            continue

        target_bytes = target.read_bytes()
        target_sha = compute_sha256(target)
        is_identical = (source_bytes == target_bytes) and (source_sha == target_sha)

        if not is_identical:
            all_in_sync = False

        results.append((target, target_sha, is_identical))

    return all_in_sync, results


def sync_skill_to_targets(
    source_path: Path,
    targets: List[Path],
) -> List[Tuple[Path, str, bool]]:
    """Synchronize source SKILL.md to all target destinations atomically with verification.

    Returns:
        list_of_(target_path, new_sha256, success)
    """
    if not source_path.is_file():
        raise FileNotFoundError(f"Authoritative source skill not found at: {source_path}")

    source_sha = compute_sha256(source_path)
    source_bytes = source_path.read_bytes()

    results = []
    for target in targets:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            # Atomic write via temp file
            temp_target = target.with_suffix(".tmp_sync")
            temp_target.write_bytes(source_bytes)
            temp_target.replace(target)

            # Verify byte-identical copy
            written_sha = compute_sha256(target)
            if written_sha == source_sha:
                results.append((target, written_sha, True))
            else:
                results.append((target, written_sha, False))
        except Exception as exc:
            results.append((target, str(exc), False))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync tts-cli SKILL.md to consuming repos with SHA-256 verification"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check synchronization status without modifying files",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Perform atomic copy to all discovered/specified targets",
    )
    parser.add_argument(
        "--target",
        type=Path,
        action="append",
        help="Explicit target file path to check/sync (can be specified multiple times)",
    )

    args = parser.parse_args()

    repo_root = find_repo_root()
    source = get_source_skill_path(repo_root)

    if not source.is_file():
        print(f"❌ Source skill file not found: {source}")
        return 1

    source_sha = compute_sha256(source)
    print(f"Authoritative Source: {source}")
    print(f"SHA-256 Digest:       {source_sha}")
    print("=" * 65)

    targets = args.target if args.target else discover_default_targets(repo_root)

    if not targets:
        print("ℹ️  No consuming repository targets found.")
        return 0

    if args.check or not args.sync:
        all_ok, results = check_skill_sync(source, targets)
        print("Target Status:")
        for target, sha_or_msg, is_synced in results:
            status = "✅ IN SYNC" if is_synced else f"❌ OUT OF SYNC ({sha_or_msg})"
            print(f"  {str(target):60} {status}")

        if not all_ok:
            print("\nRun with `--sync` to synchronize out-of-sync targets.")
            return 1 if args.check else 0
        return 0

    if args.sync:
        print("Synchronizing targets...")
        results = sync_skill_to_targets(source, targets)
        all_success = True
        for target, sha, success in results:
            status = f"✅ SYNCED (SHA-256: {sha[:12]}...)" if success else f"❌ FAILED ({sha})"
            if not success:
                all_success = False
            print(f"  {str(target):60} {status}")
        return 0 if all_success else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
