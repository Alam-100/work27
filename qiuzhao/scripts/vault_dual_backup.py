# -*- coding: utf-8 -*-
"""Dual backup for Obsidian vault: push GitHub + refresh D: mirror.

E: 盘机械盘随时可能再损坏。策略：
1. 优先在 E:\\obsidian 正常 commit/push；
2. 一旦 E: 的 .git 损坏/不可用，自动改走 D:\\backup\\my-obsidian-mirror
   同步可读工作树 → commit → push origin → 再用镜像 .git 修复 E:；
3. 任何 vault 改动后都应调用本脚本；禁止只写 E: 不推远程。

Usage:
  python qiuzhao/scripts/vault_dual_backup.py
  python qiuzhao/scripts/vault_dual_backup.py -m "vault: note"
  python qiuzhao/scripts/vault_dual_backup.py --skip-push   # 仅对齐 D: 镜像
  python qiuzhao/scripts/vault_dual_backup.py --force-mirror  # 强制走镜像路径
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(r"E:\obsidian")
MIRROR = Path(r"D:\backup\my-obsidian-mirror")
REMOTE = "https://github.com/Alam-100/my-obsidian.git"
VAULT_REL = Path("My_docs")


def run(
    cmd: list[str],
    cwd: Path | None = None,
    *,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), f"(cwd={cwd})" if cwd else "", flush=True)
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        err = (exc.stderr or "") if isinstance(exc.stderr, str) else f"timeout after {timeout}s"
        return subprocess.CompletedProcess(cmd, 124, out, err)


def ensure_utf8_sample(root: Path) -> None:
    qiuzhao = root / VAULT_REL / "秋招"
    samples = [
        qiuzhao / "修改日志.md",
        qiuzhao / "04_情报" / "来源日志.md",
        qiuzhao / "02_情报库" / "_索引.md",
    ]
    failures: list[str] = []
    ok = 0
    for sample in samples:
        if not sample.exists():
            continue
        try:
            raw = sample.read_bytes()
            raw.decode("utf-8")
            if b"\x00" in raw:
                raise UnicodeDecodeError("utf-8", raw, 0, 1, "NUL byte found")
        except UnicodeDecodeError as exc:
            failures.append(f"{sample}: {exc}")
            continue
        ok += 1
        print(f"utf8-ok: {sample}", flush=True)
    if failures:
        raise SystemExit("UTF-8 sample check failed; refusing to push:\n" + "\n".join(failures))
    if not ok:
        raise SystemExit(f"missing UTF-8 samples under {root / VAULT_REL}")


def git_usable(cwd: Path, *, timeout: float = 20.0) -> bool:
    """Fast probe: corrupt HDD-backed git repos can hang indefinitely."""
    if not (cwd / ".git").exists():
        return False
    probe = run(["git", "rev-parse", "--verify", "HEAD"], cwd=cwd, timeout=timeout)
    if probe.returncode != 0:
        print(f"git unusable at {cwd}: {(probe.stderr or probe.stdout).strip()[:240]}", flush=True)
        return False
    st = run(["git", "status", "--porcelain"], cwd=cwd, timeout=timeout)
    if st.returncode != 0:
        print(f"git unusable at {cwd}: {(st.stderr or st.stdout).strip()[:240]}", flush=True)
        return False
    return True


def commit_all(cwd: Path, message: str | None) -> bool:
    """Stage+commit if dirty. Returns True if a commit was created."""
    st = run(["git", "status", "--porcelain"], cwd=cwd, timeout=30)
    if st.returncode != 0:
        raise SystemExit(st.stderr or st.stdout)
    if not st.stdout.strip():
        print(f"working tree clean at {cwd}; skip commit")
        return False
    add = run(["git", "add", "-A"], cwd=cwd, timeout=60)
    if add.returncode != 0:
        raise SystemExit(add.stderr or add.stdout)
    msg = message or f"vault backup: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    commit = run(["git", "commit", "-m", msg], cwd=cwd, timeout=90)
    out = (commit.stdout or "") + (commit.stderr or "")
    if commit.returncode != 0 and "nothing to commit" not in out:
        raise SystemExit(out)
    print(out.strip() or "committed")
    return True


def push_origin(cwd: Path) -> str:
    push = run(["git", "push", "origin", "main"], cwd=cwd, timeout=120)
    if push.returncode != 0:
        raise SystemExit(push.stderr or push.stdout)
    print((push.stdout or push.stderr).strip() or "pushed")
    head = run(["git", "rev-parse", "HEAD"], cwd=cwd, timeout=20)
    return (head.stdout or "").strip()


def sync_workdir_to_mirror() -> None:
    """Copy readable My_docs from E: into D: mirror (exclude .git)."""
    src = REPO / VAULT_REL
    dst = MIRROR / VAULT_REL
    if not src.is_dir():
        raise SystemExit(f"missing vault worktree: {src}")
    MIRROR.mkdir(parents=True, exist_ok=True)
    dst.mkdir(parents=True, exist_ok=True)

    # Prefer robocopy on Windows for resilience; fall back to shutil.
    robocopy = shutil.which("robocopy")
    if robocopy:
        # /E copy subdirs incl empty; /R:1 /W:1 retry lightly; /NFL /NDL quieter;
        # /XD skip .git; exit codes 0-7 are success for robocopy
        cmd = [
            robocopy,
            str(src),
            str(dst),
            "/E",
            "/R:1",
            "/W:1",
            "/NFL",
            "/NDL",
            "/NJH",
            "/NJS",
            "/XD",
            ".git",
        ]
        print("+", " ".join(cmd))
        cp = subprocess.run(
            cmd,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=300,
        )
        if cp.returncode >= 8:
            raise SystemExit(f"robocopy failed rc={cp.returncode}: {cp.stdout}\n{cp.stderr}")
        print(f"robocopy ok rc={cp.returncode}")
        return

    # shutil fallback
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d != ".git"]
        rel = Path(root).relative_to(src)
        target_dir = dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            s = Path(root) / name
            t = target_dir / name
            try:
                shutil.copy2(s, t)
            except OSError as exc:
                print(f"skip unreadable: {s} ({exc})")


def ensure_mirror_repo() -> None:
    if not (MIRROR / ".git").exists():
        MIRROR.parent.mkdir(parents=True, exist_ok=True)
        if MIRROR.exists() and any(MIRROR.iterdir()):
            # non-empty without .git — clone into temp then is hard; require clean
            raise SystemExit(f"mirror exists without .git: {MIRROR}")
        clone = run(["git", "clone", REMOTE, str(MIRROR)], timeout=180)
        if clone.returncode != 0:
            raise SystemExit(clone.stderr or clone.stdout)
        print(clone.stdout or clone.stderr)
        return
    if not git_usable(MIRROR):
        repair_mirror_git_from_remote()
    pull = run(["git", "pull", "--ff-only", "origin", "main"], cwd=MIRROR, timeout=120)
    if pull.returncode != 0:
        # try fetch + reset soft? Prefer fail loud rather than destroy local mirror edits
        print("warn: mirror pull failed; continue with local mirror state")
        print((pull.stderr or pull.stdout).strip()[:400])
    else:
        print((pull.stdout or pull.stderr).strip() or "mirror pulled")


def repair_mirror_git_from_remote() -> None:
    """Refresh only D: mirror .git from GitHub while keeping the mirror worktree."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    temp = MIRROR.parent / f".my-obsidian-git-refresh-{stamp}"
    old_git = MIRROR / ".git"
    old_dest = MIRROR / f".git.corrupt-{stamp}"
    print(f"D: mirror git unusable; refresh .git via clean clone: {temp}", flush=True)
    clone = run(["git", "clone", REMOTE, str(temp)], timeout=180)
    if clone.returncode != 0:
        raise SystemExit(clone.stderr or clone.stdout)
    if old_git.exists():
        old_git.rename(old_dest)
        print(f"quarantined D: mirror .git -> {old_dest}", flush=True)
    shutil.copytree(temp / ".git", old_git)
    shutil.rmtree(temp, ignore_errors=True)
    run(["git", "remote", "set-url", "origin", REMOTE], cwd=MIRROR, timeout=20)
    if not git_usable(MIRROR):
        raise SystemExit(f"D: mirror git still unusable after refresh: {MIRROR}")
    print("D: mirror .git refreshed from GitHub", flush=True)


def quarantine_corrupt_git(repo: Path) -> Path | None:
    git_dir = repo / ".git"
    if not git_dir.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = repo / f".git.corrupt-{stamp}"
    print(f"quarantine {git_dir} -> {dest}")
    git_dir.rename(dest)
    return dest


def repair_e_git_from_mirror() -> None:
    """Replace E: .git with a copy of healthy D: mirror .git so future commits work."""
    if not git_usable(MIRROR):
        raise SystemExit("cannot repair E: — mirror git unusable")
    quarantine_corrupt_git(REPO)
    src = MIRROR / ".git"
    dst = REPO / ".git"
    print(f"copy .git {src} -> {dst}")
    shutil.copytree(src, dst)
    # Point remote just in case
    run(["git", "remote", "set-url", "origin", REMOTE], cwd=REPO, timeout=20)
    st = run(["git", "status", "--porcelain"], cwd=REPO, timeout=30)
    if st.returncode != 0:
        raise SystemExit(f"E: git still broken after repair: {st.stderr or st.stdout}")
    print("E: .git repaired from D: mirror")
    if st.stdout.strip():
        print("note: E: working tree still differs from repaired index:")
        print(st.stdout[:800])


def push_via_e(message: str | None) -> str:
    ensure_utf8_sample(REPO)
    commit_all(REPO, message)
    return push_origin(REPO)


def push_via_mirror(message: str | None, *, repair_e: bool = True) -> str:
    print("=== fallback: push via D: mirror (E: git unsafe) ===")
    ensure_mirror_repo()
    ensure_utf8_sample(REPO)
    sync_workdir_to_mirror()
    ensure_utf8_sample(MIRROR)
    commit_all(MIRROR, message)
    head = push_origin(MIRROR)
    if repair_e:
        try:
            repair_e_git_from_mirror()
        except SystemExit as exc:
            print(f"warn: E: .git repair skipped: {exc}")
    return head


def sync_mirror_from_remote(expected_head: str) -> None:
    ensure_mirror_repo()
    # If we just pushed from mirror, pull is no-op; if pushed from E:, refresh D:
    pull = run(["git", "pull", "--ff-only", "origin", "main"], cwd=MIRROR, timeout=120)
    if pull.returncode != 0:
        raise SystemExit(pull.stderr or pull.stdout)
    print((pull.stdout or pull.stderr).strip() or "mirror synced")
    head = run(["git", "rev-parse", "HEAD"], cwd=MIRROR, timeout=20)
    mirror_head = (head.stdout or "").strip()
    print(f"repo/push HEAD={expected_head}")
    print(f"mirror HEAD={mirror_head}")
    if expected_head and mirror_head and expected_head != mirror_head:
        raise SystemExit("mirror HEAD mismatch after sync")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", "-m", default=None)
    ap.add_argument("--skip-push", action="store_true", help="only refresh D: mirror from remote")
    ap.add_argument(
        "--force-mirror",
        action="store_true",
        help="skip E: git and always sync/push via D: mirror",
    )
    ap.add_argument(
        "--no-repair-e",
        action="store_true",
        help="when using mirror path, do not replace E: .git",
    )
    args = ap.parse_args()

    if not REPO.exists():
        raise SystemExit(f"repo missing: {REPO}")

    if args.skip_push:
        # Align D: only
        if git_usable(REPO):
            head = run(["git", "rev-parse", "HEAD"], cwd=REPO, timeout=20).stdout.strip()
        else:
            ensure_mirror_repo()
            head = run(["git", "rev-parse", "HEAD"], cwd=MIRROR, timeout=20).stdout.strip()
        sync_mirror_from_remote(head)
        print("dual-backup OK (skip-push)")
        return 0

    used_mirror = False
    if args.force_mirror or not git_usable(REPO):
        head = push_via_mirror(args.message, repair_e=not args.no_repair_e)
        used_mirror = True
    else:
        try:
            head = push_via_e(args.message)
        except SystemExit as exc:
            print(f"E: push failed ({exc}); falling back to D: mirror")
            head = push_via_mirror(args.message, repair_e=not args.no_repair_e)
            used_mirror = True

    if not used_mirror:
        sync_mirror_from_remote(head)
    else:
        # already on mirror HEAD
        print(f"mirror was push vehicle; HEAD={head}")

    print("dual-backup OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
