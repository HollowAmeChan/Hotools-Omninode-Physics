#!/usr/bin/env python3
"""把本扩展仓库打包成可安装 ZIP（供父仓"安装扩展…"使用）。

产物形态与仓库布局一致：ZIP 根下直接是扩展目录内容（清单 + 包目录），
不套额外的顶层目录，因此父仓安装器解压后即可直接发现：

    <插件>/OmniNode/extensions/<清单 identifier>/
        extension.json
        PhysicsWorld/...

用法：
    python tools/build_extension_zip.py --output _dist/HoTools-Omninode-Physics.zip
    python tools/build_extension_zip.py --abi py313 --output _dist/ext-py313.zip
    python tools/build_extension_zip.py --source-only --output _dist/ext-src.zip

选项：
    --abi {py311,py313}   只打包该 Python ABI 的原生运行时；省略则两个都打（若存在）
    --source-only         不包含 native/runtime/<abi>/ 下的 pyd（纯源码包）
    --version VERSION     把版本号写进包内清单（只影响 ZIP 内容，不改仓库里的
                          extension.json）。CI 用时间戳版本戳，与主仓发布线一致。
    --repo-root PATH      仓库根，默认脚本所在目录的上一级
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile


MANIFEST_FILENAME = "extension.json"
NATIVE_RUNTIME = PurePosixPath("PhysicsWorld/native/runtime")

# 永不入包：开发产物与缓存
EXCLUDED_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".fetch-cache",
    "_dist",  # 打包输出目录：否则第二次打包会把上一次的 ZIP 打进包里
    "build",
    "$Recycle.Bin",
    "obj",
    "Library",  # Unity oracle 缓存（实测约 960 MB）
    "Logs",
    "Temp",
    "UserSettings",
}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".blend1", ".bak", ".orig", ".rej")


def load_manifest(repo_root: Path) -> dict:
    path = repo_root / MANIFEST_FILENAME
    if not path.is_file():
        raise SystemExit(f"缺少清单：{path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SystemExit(f"清单不是合法 JSON：{exc}") from exc
    if not isinstance(data, dict) or not str(data.get("identifier") or "").strip():
        raise SystemExit("清单必须包含非空的 identifier")
    return data


def iter_files(repo_root: Path, abi: str | None, source_only: bool, output: Path | None = None):
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        if output is not None and path == output:
            continue
        relative = PurePosixPath(path.relative_to(repo_root).as_posix())
        if any(part in EXCLUDED_DIR_NAMES for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        if relative.is_relative_to(NATIVE_RUNTIME):
            rest = relative.relative_to(NATIVE_RUNTIME)
            if source_only:
                continue
            if abi is not None and rest.parts and rest.parts[0] != abi:
                continue
        yield path, relative


def validate_members(members: list[str], abi: str | None) -> None:
    if not members:
        raise SystemExit("包内没有任何文件")
    if any(member.startswith("PhysicsWorld/native/runtime/") for member in members):
        if abi is None:
            raise SystemExit("未指定 --abi 时不应包含原生运行时")
    other = {"py311", "py313"} - ({abi} if abi else set())
    for member in members:
        for candidate in other:
            if member.startswith(f"PhysicsWorld/native/runtime/{candidate}/"):
                raise SystemExit(f"包内混入了非目标 ABI：{member}")
    for required in (MANIFEST_FILENAME, "PhysicsWorld/omninode_registration.py"):
        if required not in members:
            raise SystemExit(f"缺少必需文件：{required}")


def build(
    repo_root: Path,
    output: Path,
    *,
    abi: str | None,
    source_only: bool,
    version: str | None = None,
) -> tuple[int, int]:
    manifest = load_manifest(repo_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)

    # 版本戳只作用于包内清单副本，仓库里的 extension.json 保持开发版本号。
    stamped_manifest: bytes | None = None
    if version:
        stamped = dict(manifest)
        stamped["version"] = version
        stamped_manifest = (
            json.dumps(stamped, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")

    members: list[str] = []
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as archive:
        for source, relative in iter_files(repo_root, abi, source_only, output):
            name = relative.as_posix()
            if stamped_manifest is not None and name == MANIFEST_FILENAME:
                archive.writestr(name, stamped_manifest)
            else:
                archive.write(source, name)
            members.append(name)

    validate_members(members, abi)
    size_mib = output.stat().st_size / (1024 * 1024)
    print(
        f"Built {output} ({size_mib:.2f} MiB, {len(members)} files, "
        f"identifier={manifest['identifier']}, "
        f"version={version or manifest.get('version') or '?'}, "
        f"abi={abi or 'none'}{', source-only' if source_only else ''})"
    )
    return len(members), int(size_mib * 1024)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--abi", choices=("py311", "py313"), default=None)
    parser.add_argument(
        "--source-only",
        action="store_true",
        help="不包含 native/runtime/<abi>/ 下的 pyd",
    )
    parser.add_argument(
        "--version",
        default=None,
        help="写进包内清单的版本号（不改仓库文件）；省略则用仓库清单里的版本",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        # 脚本位于 <仓库>/PhysicsWorld/tools/，因此仓库根上溯两级
        default=Path(__file__).resolve().parents[2],
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    if not (repo_root / MANIFEST_FILENAME).is_file():
        raise SystemExit(f"不是扩展仓库根（缺少 {MANIFEST_FILENAME}）：{repo_root}")
    build(
        repo_root,
        args.output.resolve(),
        abi=args.abi,
        source_only=args.source_only,
        version=args.version,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
