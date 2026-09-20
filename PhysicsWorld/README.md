# PhysicsWorld

OmniNode 物理世界**扩展包**。外层 `Hotools-Omninode-Physics/` 是本仓库，
本目录是被父仓按 `HoTools.OmniNode.PhysicsWorld` 加载的包。

| 路径 | 作用 |
| --- | --- |
| `omninode_registration.py` | 节点/菜单声明与 `register_blender()` 生命周期钩子 |
| `native_runtime.py` | 原生模块解析（自持 `native/runtime/<abi>/`，过渡期回退父仓 `_Lib`） |
| `mc2/` `rigid/` `rigid_fracture/` `xpbd/` `spring_vrm/` `field/` `collision/` `bake/` `simple_cloth/` | 各物理解算域 |
| `native/` | 自持原生工程，产出 `hotools_physics` + `hotools_jolt` |
| `docs/` | 物理蓝图与契约 |
| `test/`、`native/tests/` | 物理回归测试 |
| `tools/` | MC2 架构审计、V1-R 验收脚本、Unity oracle |

清单、构建与契约说明见仓库根的 `../README.md`；扩展机制（内置模块 vs 用户安装扩展）
见父仓 `OmniNode/EXTENSIONS.md`。
