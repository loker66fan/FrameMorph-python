# 技术维护文档

## 1. 项目定位

本项目是一个基于 `PySide6 + Pillow + OpenCV` 的桌面图像编辑工具，当前支持：

- 图片导入与拖拽
- 裁剪
- 缩放、拉伸、旋转
- 网格变形
- 透视变换
- 文字图层
- 高清导出与超分增强

## 2. 当前目录结构

```text
FrameMorph-python/
├── .github/
│   └── workflows/
│       └── windows-portable-build.yml
├── main.py
├── core/
│   ├── crop_controller.py
│   ├── history_manager.py
│   ├── image_model.py
│   ├── mesh_warp_controller.py
│   ├── perspective_controller.py
│   ├── text_controller.py
│   └── transform_controller.py
├── ui/
│   ├── crop_view.py
│   ├── export_mixin.py
│   ├── export_support.py
│   ├── main_window.py
│   ├── transform_view.py
│   └── warp_view.py
├── utils/
│   └── image_utils.py
├── models/
│   └── opencv_dnn_superres/
├── docs/
│   ├── TECHNICAL.md
│   └── USER_GUIDE.md
├── release/
│   ├── offline-packages/
│   ├── windows-build-output/
│   └── windows-portable/
│       ├── build_windows.bat
│       ├── FrameMorph-python.spec
│       ├── python-installer/
│       ├── requirements-windows-build.txt
│       └── wheelhouse/
├── scripts/
│   ├── build_windows_offline_package.py
│   └── prepare_windows_offline_wheels.py
├── requirements.txt
└── 方案.md
```

## 3. 模块职责

### `main.py`

- 应用入口
- 创建 `QApplication`
- 展示主窗口
- 在 GUI 打包环境下仅当 `sys.stderr` 可用时才启用 `faulthandler`

### `core/`

- 放纯业务控制逻辑
- 不直接依赖主窗口

重点模块：

- `image_model.py`
  - 当前图像、原图、预览图、文字图层状态
- `history_manager.py`
  - 撤销/重做状态栈
- `transform_controller.py`
  - 缩放、拉伸、旋转
- `mesh_warp_controller.py`
  - 网格变形，当前是 TPS 反向映射实现
- `perspective_controller.py`
  - 透视变换
- `text_controller.py`
  - 文字图层绘制与坐标变换

### `ui/`

- 放界面和交互组织代码

重点模块：

- `main_window.py`
  - 主界面
  - 控件创建
  - 各功能模式切换
  - 调用 `core/` 与 `utils/`
- `export_mixin.py`
  - 导出面板构建
  - 导出预览
  - 模型识别与模型下载入口
  - 导出任务窗口与导出流程编排
  - `torch` 缺失时自动禁用 `SRCNN`
  - `dnn_superres` 优先复用本地 `models/opencv_dnn_superres/` 中的模型
- `transform_view.py`
  - 主画布 `QGraphicsView`
  - 图片显示、覆盖层、拖拽、缩放
- `export_support.py`
  - 导出相关支持能力
  - 超分模型配置
  - 模型下载线程
  - 导出线程

### `utils/`

- 放图像工具函数和跨模块通用逻辑

重点模块：

- `image_utils.py`
  - PIL / Qt / OpenCV 互转
  - 图像保存
  - 高清增强
  - `dnn_superres` 模型文件识别
  - `dnn_superres` 运行时依赖 `opencv-contrib-python`

## 4. 关键数据流

### 4.1 图片编辑主链路

1. `MainWindow.load_image()`
2. `ImageModel.load()`
3. 用户在右侧面板操作
4. `MainWindow` 调用对应 `Controller`
5. 结果写回 `ImageModel`
6. `HistoryManager` 记录状态
7. 画布刷新

### 4.2 导出主链路

1. `MainWindow.export_image_dialog()`
2. `MainWindow._build_export_image()`
3. 选择增强器：
   - 经典超分
   - SRCNN
   - OpenCV `dnn_superres`
4. `ExportImageThread`
5. `utils.image_utils.save_image_file()`

### 4.3 导出预览优化链路

当前导出预览不是对整张原图反复做增强，而是：

1. 先把当前图像渲染成缩略图
2. 只对缩略图做增强
3. 使用参数级缓存复用结果

这部分是当前最重要的性能优化点之一。

## 5. Windows 打包与离线构建链路

### 5.1 在线打包链路

- GitHub Actions 工作流：`.github/workflows/windows-portable-build.yml`
- Windows 本地脚本：`release/windows-portable/build_windows.bat`
- Windows 打包专用依赖清单：`release/windows-portable/requirements-windows-build.txt`
- PyInstaller 配置：`release/windows-portable/FrameMorph-python.spec`

当前约束：

- 离线 wheel 目标解释器固定为 Python 3.11 x64
- Windows 打包依赖使用 `opencv-contrib-python`，保证 `dnn_superres` 可用
- `SRCNN` 不是默认打包能力，因为默认离线依赖包不包含 `torch`
- 可选携带官方离线 Python 3.11 安装器，解决目标机器无 Python 预装的问题

### 5.2 离线打包链路

离线打包支持依赖以下目录和脚本：

- `release/windows-portable/wheelhouse/`
- `release/windows-portable/python-installer/`
- `scripts/prepare_windows_offline_wheels.py`
- `scripts/build_windows_offline_package.py`
- `release/offline-packages/`

约定如下：

- `wheelhouse/` 用来存放 Windows 打包所需的离线 `.whl`
- `python-installer/` 用来存放官方离线 Windows Python 安装器
- `build_windows.bat` 会优先从本地 `wheelhouse/` 用 `--no-index` 安装依赖
- 当目标机器缺少 Python 3.11 时，`build_windows.bat` 会优先尝试使用或安装本地私有 Python 运行时
- `release/offline-packages/` 用来生成可直接拷到无网 Windows 机器上的离线压缩包

### 5.3 哪些内容应提交到 GitHub

应提交：

- 打包脚本和说明文档
- `requirements-windows-build.txt`
- `scripts/prepare_windows_offline_wheels.py`
- `scripts/build_windows_offline_package.py`
- `wheelhouse/README.md`
- `python-installer/README.md`
- `release/offline-packages/.gitkeep`

不应提交：

- `wheelhouse/` 中实际下载的 `.whl`
- `python-installer/` 中实际下载的 `.exe`
- `release/offline-packages/` 中实际生成的离线 ZIP
- `release/windows-build-output/` 中实际构建产物

这些二进制内容属于发布或传输产物，不应进入仓库历史。

## 6. 最近完成的结构优化

### 已完成

- 将导出支持逻辑从 `ui/main_window.py` 拆到 `ui/export_support.py`
- 将导出 UI 与导出流程从 `ui/main_window.py` 拆到 `ui/export_mixin.py`
- 将导出预览改为缩略图增强 + 缓存
- 增加 `dnn_superres` 模型识别与匹配校验
- 增加后台导出线程、进度、ETA、取消导出
- 将运行时 OpenCV 依赖切换为 `opencv-contrib-python`
- 增加 Windows 离线打包依赖清单、离线 wheel 准备脚本与离线 ZIP 生成脚本
- 增加无 Python 预装场景下的本地私有 Python 引导安装流程
- 增加 GUI 打包环境下的 `faulthandler` 兼容处理
- 在缺少 `torch` 时自动禁用 `SRCNN`

### 当前仍然偏重的模块

- `ui/main_window.py`

当前仍然承担：

- 所有面板构建
- 大量 UI 事件连接
- 文本图层交互逻辑

后续建议继续拆分为：

- `ui/panels/text_panel.py`
- `ui/panels/transform_panel.py`
- `ui/panels/mesh_panel.py`

## 7. 维护建议

### 7.1 新增功能时的放置原则

- 纯算法或图像处理逻辑：优先放 `core/` 或 `utils/`
- 后台线程和导出/下载支持：放 `ui/export_support.py` 或独立 support 模块
- 仅界面拼装逻辑：放 `ui/`

### 7.2 修改导出功能时

优先查看：

- `ui/export_mixin.py`
- `ui/export_support.py`
- `utils/image_utils.py`

### 7.3 修改预览性能时

优先查看：

- `MainWindow.update_export_comparison_preview()`
- `scaled_preview_image()`
- `MeshWarpController._profile()`

### 7.4 修改 `dnn_superres` 时

优先查看：

- `DNN_SUPERRES_MODEL_SPECS`
- `infer_dnn_model_metadata()`
- `enhance_image_dnn_superres()`

### 7.5 修改 Windows 打包链路时

优先查看：

- `release/windows-portable/build_windows.bat`
- `release/windows-portable/requirements-windows-build.txt`
- `.github/workflows/windows-portable-build.yml`
- `scripts/prepare_windows_offline_wheels.py`
- `scripts/build_windows_offline_package.py`

## 8. 常见问题定位

### 导出预览失败

优先检查：

- 模型文件路径是否有效
- 模型名与倍率是否和 `.pb` 文件一致
- OpenCV 是否包含 `dnn_superres`

### 导出很慢

优先判断：

- 是否使用了超分模型
- 是否是大图
- 是否在导出而不是预览

### 右侧面板拥挤

优先修改：

- `main_window.py` 的面板布局
- 是否能继续拆成子面板模块

### Windows 打包失败

优先检查：

- 是否使用 Python 3.11 x64
- `python-installer/` 中是否存在 `python-3.11.9-amd64.exe`
- `wheelhouse/` 中是否包含 `pefile`、`pywin32-ctypes`、`pywin32`
- `requirements-windows-build.txt` 是否和打包脚本保持一致
- 是否误把离线 ZIP 当作仓库源码直接在压缩包内部运行而未完整解压

## 9. 后续重构建议

建议按以下顺序继续演进：

1. 拆分 `main_window.py` 中各面板构建代码
2. 抽离导出预览缓存为独立 helper
3. 给 `core/` 增加更明确的类型定义
4. 为导出增强和控制器补最小自动化测试
