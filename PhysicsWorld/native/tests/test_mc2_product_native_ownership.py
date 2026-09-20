"""Source-level ownership gates for the MC2 product native path."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHYSICS_ROOT = ROOT.parent  # 扩展仓库根（owns mc2/, rigid/）
PLUGIN_ROOT = ROOT.parents[3]
# 物理原生源码现位于本扩展 native/src（mc2 子目录），枢纽文件为 hotools_physics.cpp
NATIVE_SRC = ROOT / "src"
PARENT_NATIVE_SRC = PLUGIN_ROOT / "_native" / "src"
MC2_PYTHON = (
    PHYSICS_ROOT / "mc2"
)


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_v0_native_owner_sources_are_deleted() -> None:
    for leaf in (
        "mc2_context_core.cpp",
        "mc2_context_frame_step.cpp",
        "mc2_context_helpers.hpp",
        "mc2_context_interaction.cpp",
        "mc2_context_internal.hpp",
        "mc2_context_readback.cpp",
        "mc2_context_static.cpp",
    ):
        assert not (NATIVE_SRC / leaf).exists()


def test_whole_domain_self_has_no_v0_owner_dependency() -> None:
    source = _source(NATIVE_SRC / "mc2" / "mc2_whole_domain_self.cpp")
    assert "WholeDomainSelfState" in source
    for forbidden in (
        "mc2_context_internal.hpp",
        "mc2_context_helpers.hpp",
        "Mc2ContextV0",
        "mc2_internal",
    ):
        assert forbidden not in source


def test_frame_orientations_have_no_v0_owner_dependency() -> None:
    source = _source(NATIVE_SRC / "mc2" / "mc2_frame_orientations.cpp")
    for forbidden in (
        "mc2_context_internal.hpp",
        "mc2_context_helpers.hpp",
        "Mc2ContextV0",
        "mc2_internal",
    ):
        assert forbidden not in source


def test_product_topology_uses_only_v1_static_fingerprints() -> None:
    source = _source(MC2_PYTHON / "topology.py")
    assert "mc2_mesh_static_fingerprint_v1" in source
    assert "mc2_bone_static_fingerprint_v1" in source
    assert "static_fingerprint_v0" not in source


def test_bone_product_constraint_soak_has_no_legacy_owner_dependency() -> None:
    source = _source(
        MC2_PYTHON.parent
        / "test"
        / "test_blender_mc2_bone_product_constraint_soak.py"
    )
    for forbidden in (
        "_physicsMC2BoneClothTaskV0Oracle",
        "_physicsMC2BoneSpringTaskV0Oracle",
        "MC2TaskSpec(",
        'data["native_context"]',
        "import interaction_scope",
        "Mc2InteractionV0",
    ):
        assert forbidden not in source


def test_three_setup_product_soak_has_no_legacy_owner_dependency() -> None:
    source = _source(
        MC2_PYTHON.parent
        / "test"
        / "test_blender_mc2_product_mixed_output_soak.py"
    )
    for forbidden in (
        "_physicsMC2",
        "MC2TaskSpec(",
        'data["native_context"]',
        "import interaction_scope",
        "Mc2InteractionV0",
        "collect_mc2_mesh_product_domain",
    ):
        assert forbidden not in source
