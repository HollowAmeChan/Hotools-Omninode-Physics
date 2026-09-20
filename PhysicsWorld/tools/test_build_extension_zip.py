#!/usr/bin/env python3
"""打包工具的冒烟测试（纯标准库，不需要 Blender、不需要原生 pyd）。

    python PhysicsWorld/tools/test_build_extension_zip.py

覆盖三类曾经真实踩过 / 容易再犯的问题：
  1. `_dist/` 下的历史产物把自己的 ZIP 打进包里（自包含）；
  2. `--source-only` 泄漏 `native/runtime/<abi>/` 的原生模块；
  3. `--abi` 把两个 ABI 混进同一个包。
"""

from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_extension_zip as pack  # noqa: E402


def make_repo(root: Path) -> None:
    (root / "extension.json").write_text(
        json.dumps({"identifier": "PhysicsWorld", "version": "0.0.0"}),
        encoding="utf-8",
    )
    pkg = root / "PhysicsWorld"
    (pkg / "native" / "runtime" / "py311").mkdir(parents=True)
    (pkg / "native" / "runtime" / "py313").mkdir(parents=True)
    (pkg / "tools").mkdir(parents=True)
    (pkg / "omninode_registration.py").write_text("x = 1\n", encoding="utf-8")
    (pkg / "__init__.py").write_text("y = 2\n", encoding="utf-8")
    for abi in ("py311", "py313"):
        (pkg / "native" / "runtime" / abi / "hotools_physics.pyd").write_bytes(b"\0")
    # 历史产物：修复前会被打进包里
    dist = root / "_dist"
    dist.mkdir()
    (dist / "old.zip").write_bytes(b"PK\x03\x04old")
    (dist / "note.txt").write_text("keep out\n", encoding="utf-8")
    # 缓存目录
    cache = pkg / "__pycache__"
    cache.mkdir()
    (cache / "mod.cpython-311.pyc").write_bytes(b"\0")


def members(archive: Path) -> set[str]:
    with zipfile.ZipFile(archive) as zf:
        return set(zf.namelist())


def check(label: str, condition: bool, detail: str = "") -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")
    return condition


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        make_repo(repo)
        out = repo / "_dist" / "src.zip"

        # 连续打两次：第二次时 _dist 里已经有第一个 ZIP，正是自包含 bug 的触发条件
        pack.build(repo, out, abi=None, source_only=True)
        first = members(out)
        pack.build(repo, out, abi=None, source_only=True)
        second = members(out)

        failures += not check(
            "source-only 包不含 _dist 产物",
            not any(m.startswith("_dist/") for m in second),
        )
        failures += not check(
            "连续打包结果稳定（不会把上一次的 ZIP 吃进来）",
            first == second,
            f"first={len(first)} second={len(second)}",
        )
        failures += not check(
            "source-only 包不含 native/runtime",
            not any(m.startswith("PhysicsWorld/native/runtime/") for m in second),
        )
        failures += not check(
            "不含 __pycache__",
            not any("__pycache__" in m for m in second),
        )
        failures += not check(
            "含清单与注册模块",
            {"extension.json", "PhysicsWorld/omninode_registration.py"} <= second,
        )

        # 单 ABI 打包
        for abi in ("py311", "py313"):
            one = repo / "_dist" / f"{abi}.zip"
            pack.build(repo, one, abi=abi, source_only=False)
            got = members(one)
            wanted = f"PhysicsWorld/native/runtime/{abi}/hotools_physics.pyd"
            other = "py313" if abi == "py311" else "py311"
            failures += not check(
                f"--abi {abi} 只含本 ABI 原生模块",
                wanted in got
                and not any(f"native/runtime/{other}/" in m for m in got),
            )

        # 未指定 ABI 却带上了原生运行时 -> 必须报错
        try:
            pack.validate_members(
                ["extension.json", "PhysicsWorld/omninode_registration.py",
                 "PhysicsWorld/native/runtime/py311/hotools_physics.pyd"],
                None,
            )
        except SystemExit:
            failures += not check("未指定 --abi 时带原生运行时会被拒绝", True)
        else:
            failures += not check("未指定 --abi 时带原生运行时会被拒绝", False)

        # 混 ABI -> 必须报错
        try:
            pack.validate_members(
                ["extension.json", "PhysicsWorld/omninode_registration.py",
                 "PhysicsWorld/native/runtime/py311/a.pyd",
                 "PhysicsWorld/native/runtime/py313/a.pyd"],
                "py311",
            )
        except SystemExit:
            failures += not check("混入非目标 ABI 会被拒绝", True)
        else:
            failures += not check("混入非目标 ABI 会被拒绝", False)

        # 缺必需文件 -> 必须报错
        try:
            pack.validate_members(["extension.json"], None)
        except SystemExit:
            failures += not check("缺 omninode_registration.py 会被拒绝", True)
        else:
            failures += not check("缺 omninode_registration.py 会被拒绝", False)

    print()
    if failures:
        print(f"{failures} 项失败")
        return 1
    print("打包工具冒烟测试全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
