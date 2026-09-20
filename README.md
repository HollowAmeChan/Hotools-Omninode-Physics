# HoTools-Omninode-Physics

OmniNode 的**物理世界扩展**独立仓库。

> 本地布局说明：本仓库嵌套在 HoTools 插件的 `OmniNode/PhysicsWorld/` 目录内，
> 保持 `HoTools.OmniNode.PhysicsWorld` 包路径不变。物理包有 283 处父级相对导入
> （`from ..names import ...`、`from ... import ...`），因此仓库**不能**搬到文件
> 系统根部，只能嵌套在插件树内。

## 内容

| 路径 | 作用 |
| --- | --- |
| `omninode_registration.py` | 对 OmniNode 注册器公开的节点/菜单声明与 `register_blender()` 生命周期钩子 |
| `extension.json` | 扩展清单：identifier、版本、`omninode_api` 契约、原生模块需求 |
| `mc2/` `rigid/` `rigid_fracture/` `xpbd/` `spring_vrm/` `field/` `collision/` `bake/` `simple_cloth/` | 各物理解算域 |
| `native/` | 自持原生工程，产出 `hotools_physics` + `hotools_jolt` |
| `doc/`（迁入后） | 蓝图与契约文档 |
| `test/`、`native/tests/` | 物理回归测试 |

## 原生模块

本扩展**自持**两个 pyd，产物落在 `native/runtime/<abi>/`，不写入父仓 `_Lib`：

- `hotools_physics`：MC2 / Field / XPBD / SpringVRM / RigidWriteback 内核
- `hotools_jolt`：Jolt Physics 刚体/约束后端（含 Blender 兼容 Mutex 补丁）

构建：

```bat
native\build.bat            :: py311 + py313，两个模块
native\build.bat 313        :: 只构建 Blender 5.x / py313
native\build.bat 313 physics :: 只构建 hotools_physics
```

复用父仓已下载的依赖源码（省一次 nanobind/Jolt 拉取）：

```bat
set HOTOOLS_FETCH_CACHE=<HoTools>\_native\.fetch-cache
native\build.bat 313
```

## 与父仓的契约

- 父仓通过 `OmniNode/OmniNodeRegister.py` 的扩展机制发现本扩展：
  搜索根为 `OmniNode/`（内置）与 `OmniNode/extensions/`（外置安装位）。
- 运行时原生解析顺序见父仓 `OmniNode/PhysicsWorld/native_runtime.py`：
  环境覆盖 → 本扩展 `native/runtime/<abi>/` → 父仓 `_Lib`（开发过渡回退）。
- **PropertyCurve 属父仓贮藏内容**，本扩展只是调用方（MC2 曲线参数与预设 payload），
  不复制、不扩展其原生内核。
- `omninode_api` 声明所需的 OmniNode 扩展 API 区间；不兼容时父仓会禁用本扩展并给出
  可读提示，而不会中断整个节点树注册。

## 测试

```bat
:: 物理原生内核测试（需要先构建出 runtime/<abi>/ 下的 pyd）
python native\tests\run_all.py

:: Blender 内的物理回归测试
blender.exe -b --factory-startup --python test\<case>.py
```
