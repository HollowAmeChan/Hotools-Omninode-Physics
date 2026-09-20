# HoTools-Omninode-Physics

OmniNode 的**物理世界扩展**独立仓库。

仓库布局与**用户安装后的目录逐字一致**：清单在仓库根，扩展包是一个同名子目录。
本机把仓库嵌套在插件的扩展安装位里，因此这个目录本身就是一个"已安装的扩展"：

```
<插件>/OmniNode/extensions/Hotools-Omninode-Physics/   ← 本仓库（= 用户安装后的目录）
├── extension.json        扩展清单（identifier / 版本 / API 契约 / 原生模块）
├── README.md
├── .gitignore .gitattributes
└── PhysicsWorld/         扩展包（= HoTools.OmniNode 下的子包 PhysicsWorld）
    ├── omninode_registration.py   节点/菜单声明 + Blender 生命周期钩子
    ├── native_runtime.py          原生模块解析（自持 runtime）
    ├── mc2/ rigid/ rigid_fracture/ xpbd/ spring_vrm/ field/ collision/ bake/
    ├── simple_cloth/ ui/ utils/   各物理解算域与界面
    ├── native/                    自持原生工程（hotools_physics + hotools_jolt）
    ├── docs/                      蓝图与契约
    ├── test/                      物理回归测试
    └── tools/                     架构审计、V1-R 验收、Unity oracle
```

> 为什么仓库目录名带短横线、而包名是 `PhysicsWorld`：扩展身份由清单的 `identifier`
> 决定，注册器按清单的 `package` 定位包，二者互不绑死。包内有 283 处父级相对导入
> （`from ..names import ...`），因此包必须始终位于 `HoTools.OmniNode` 命名空间下，
> 不能搬到文件系统根部。

## 原生模块

本扩展**自持**两个 pyd，产物在 `PhysicsWorld/native/runtime/<abi>/`，不写入父仓 `_Lib`：

- `hotools_physics`：MC2 / Field / XPBD / SpringVRM / RigidWriteback 内核
- `hotools_jolt`：Jolt Physics 刚体/约束后端（含 Blender 兼容 Mutex 补丁）

构建：

```bat
PhysicsWorld\native\build.bat              :: py311 + py313，两个模块
PhysicsWorld\native\build.bat 313          :: 只构建 Blender 5.x / py313
PhysicsWorld\native\build.bat 313 physics  :: 只构建 hotools_physics
```

复用父仓已下载的依赖源码：

```bat
set HOTOOLS_FETCH_CACHE=<HoTools>\_native\.fetch-cache
PhysicsWorld\native\build.bat 313
```

## 与父仓的契约

- 父仓 `OmniNode/OmniNodeRegister.py` 在三个搜索根下发现扩展：`OmniNode/`
  （插件内模块）、`OmniNode/extensions/`（插件内安装位）、Blender 用户扩展目录
  （插件只读时的回退落点）。
- 原生解析顺序见 `PhysicsWorld/native_runtime.py`：环境覆盖 → 本扩展
  `native/runtime/<abi>/` → 父仓 `_Lib`（开发过渡回退）。
- **PropertyCurve 属父仓贮藏内容**，本扩展只是调用方（MC2 曲线参数与预设 payload），
  不复制、不扩展其原生内核。
- `omninode_api` 声明所需的 OmniNode 扩展 API 区间；不兼容时父仓只禁用本扩展并
  给出可读原因，不会中断整棵节点树注册。

## 测试

```bat
:: 物理原生内核测试（需先构建出 PhysicsWorld/native/runtime/<abi>/ 下的 pyd）
python PhysicsWorld\native\tests\run_all.py

:: Blender 内的物理回归测试
blender.exe -b --factory-startup --python PhysicsWorld\test\<case>.py
```
