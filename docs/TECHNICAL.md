# 技术维护文档

## 1. 项目定位

本项目是一个基于 `PySide6 + Pillow + OpenCV`，并结合 PyMuPDF、pypdf、python-docx、openpyxl 等文档处理库的本地桌面文件处理工具，当前支持：

- 文档工作台、图片工作台和设置页一级导航
- Office / Markdown / HTML / TXT / 表格等文档转换任务
- PDF 转图片、拆分、合并、压缩、旋转、加密、解密、OCR 和文字水印处理
- 图片格式转换、压缩、裁剪、缩放和批量处理
- 图片 / PDF OCR 到 TXT、DOCX、XLSX 或可搜索 PDF
- 去水印相关的 PDF 文本处理和图片区域修复
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
│   ├── app_settings.py
│   ├── crop_controller.py
│   ├── document_tasks.py
│   ├── history_manager.py
│   ├── image_model.py
│   ├── mesh_warp_controller.py
│   ├── perspective_controller.py
│   ├── text_controller.py
│   └── transform_controller.py
├── ui/
│   ├── crop_view.py
│   ├── document_workbench.py
│   ├── export_mixin.py
│   ├── export_support.py
│   ├── main_window.py
│   ├── region_picker_dialog.py
│   ├── settings_page.py
│   ├── transform_view.py
│   ├── warp_support.py
│   └── warp_view.py
├── utils/
│   └── image_utils.py
├── models/
│   └── opencv_dnn_superres/
├── docs/
│   ├── PACKAGING.md
│   ├── RELEASE.md
│   ├── RELEASE.zh-CN.md
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
│   ├── capture_readme_screenshots.py
│   └── prepare_windows_offline_wheels.py
├── requirements.txt
└── 方案.md
```

## 3. 模块职责

### `main.py`

- 应用入口
- 创建 `QApplication`
- 加载主题、字体和输出目录等本地设置
- 展示主窗口
- 在 GUI 打包环境下仅当 `sys.stderr` 可用时才启用 `faulthandler`

### `core/`

- 放纯业务控制逻辑
- 不直接依赖主窗口

重点模块：

- `app_settings.py`
  - 主题、字体大小、默认输出目录等本地配置
  - 提供设置加载、保存和应用外观的统一入口
- `document_tasks.py`
  - 文档工作台任务定义、任务类型解析、后端检测和后台执行线程
  - 封装 Office / PDF / OCR / 图片 / 去水印相关的首批本地处理器
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
  - 一级导航注册文档工作台、图片工作台和设置页
  - 图片工作台控件创建
  - 图片工作台各功能模式切换
  - 调用 `core/` 与 `utils/`
  - 右侧按钮组改为纵向堆叠，降低低分辨率下的文字溢出风险
- `document_workbench.py`
  - 文档工作台界面
  - 模块导航、文件池、任务队列、日志、后端状态和输出目录入口
  - 调用 `core.document_tasks.DocumentTaskRunner` 执行批量任务
- `settings_page.py`
  - 设置页界面
  - 主题、字体大小、默认输出目录和环境状态刷新
- `region_picker_dialog.py`
  - 图片区域框选组件
  - 支持去水印、修复、背景填充等需要区域参数的任务
- `export_mixin.py`
  - 导出面板构建
  - 导出预览
  - 模型识别与模型下载入口
  - 导出任务窗口与导出流程编排
  - `torch` 缺失时自动禁用 `SRCNN`
  - `dnn_superres` 优先复用本地 `models/opencv_dnn_superres/` 中的模型
  - 导出面板按钮组改为单列布局，减小窄分辨率下的横向溢出
- `transform_view.py`
  - 主画布 `QGraphicsView`
  - 图片显示、覆盖层、拖拽、缩放
- `export_support.py`
  - 导出相关支持能力
  - 超分模型配置
  - 模型下载线程
  - 导出线程
- `warp_support.py`
  - 网格/透视实时预览后台线程
  - 网格最终应用后台线程

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

### 4.1 应用启动与导航链路

1. `main.py` 创建 `QApplication`
2. `core.app_settings.load_app_settings()` 加载本地配置
3. `core.app_settings.apply_app_appearance()` 应用主题和字体
4. `MainWindow` 注册文档工作台、图片工作台和设置页
5. 用户通过左侧一级导航切换工作区

### 4.2 文档任务主链路

1. `DocumentWorkbench` 根据当前模块生成文件池和目标动作
2. `resolve_task_kind()` 将模块、文件后缀和目标动作解析为具体 `task_kind`
3. `DocumentTask` 进入任务队列
4. `DocumentTaskRunner` 在后台线程中按任务执行
5. 任务状态通过 Qt 信号回写到队列和日志
6. 输出写入默认输出目录下的任务分类子目录

### 4.3 图片编辑主链路

1. `MainWindow.load_image()`
2. `ImageModel.load()`
3. 用户在右侧面板操作
4. `MainWindow` 调用对应 `Controller`
5. 结果写回 `ImageModel`
6. `HistoryManager` 记录状态
7. 画布刷新

### 4.4 导出主链路

1. `MainWindow.export_image_dialog()`
2. `MainWindow._build_export_image()`
3. 选择增强器：
   - 经典超分
   - SRCNN
   - OpenCV `dnn_superres`
4. `ExportImageThread`
5. `utils.image_utils.save_image_file()`

### 4.5 导出预览优化链路

当前导出预览不是对整张原图反复做增强，而是：

1. 先把当前图像渲染成缩略图
2. 只对缩略图做增强
3. 使用参数级缓存复用结果

这部分是当前最重要的性能优化点之一。

### 4.6 网格预览与应用链路

当前网格相关流程分成两条：

1. 实时预览
   - `MainWindow._schedule_live_preview()`
   - `LiveWarpPreviewThread`
   - 预览阶段会自动降采样，并在后台线程中执行
2. 最终应用
   - `MainWindow.apply_mesh_warp()`
   - `MeshWarpApplyThread`
   - 最终高质量输出也放到后台线程，避免主界面卡死

## 5. Windows 打包与离线构建链路

### 5.1 在线打包链路

- GitHub Actions 工作流：`.github/workflows/windows-portable-build.yml`
- Windows 本地脚本：`release/windows-portable/build_windows.bat`
- Windows 打包依赖清单：`release/windows-portable/requirements-windows-build.txt`
- PyInstaller 配置：`release/windows-portable/FrameMorph-python.spec`

当前约束：

- `requirements.txt` 负责应用运行时依赖，包含图片编辑和文档处理运行所需的 Python 库
- `requirements-windows-build.txt` 在运行时依赖之上补充 Windows 打包专用工具，供离线 wheel 准备和 PyInstaller 构建复用
- Windows 打包依赖使用 `opencv-contrib-python`，保证 `dnn_superres` 可用
- `SRCNN` 不是默认打包能力，因为默认离线依赖包不包含 `torch`
- 当前 `build_windows.bat` 已简化为依赖命令行已有可用 Python

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
- `prepare_windows_offline_wheels.py` 会根据 `requirements-windows-build.txt` 下载运行时依赖和打包额外项
- 当前 `build_windows.bat` 默认信任设备上命令行可直接调用的 Python，不再尝试自动安装包内 Python
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

- 增加文档工作台，接入文件池、任务队列、执行日志和输出目录
- 增加 `core/document_tasks.py`，集中管理文档、PDF、图片、OCR 和去水印任务执行
- 增加设置页，支持主题、字体大小、默认输出目录和环境检测
- 增加 `core/app_settings.py`，统一管理本地配置
- 增加区域框选组件，服务图片修复和去水印类任务
- 将主窗口一级导航拆分为文档工作台、图片工作台和设置页
- 将导出支持逻辑从 `ui/main_window.py` 拆到 `ui/export_support.py`
- 将导出 UI 与导出流程从 `ui/main_window.py` 拆到 `ui/export_mixin.py`
- 将导出预览改为缩略图增强 + 缓存
- 增加 `dnn_superres` 模型识别与匹配校验
- 增加后台导出线程、进度、ETA、取消导出
- 将运行时 OpenCV 依赖切换为 `opencv-contrib-python`
- 增加 Windows 离线打包依赖清单、离线 wheel 准备脚本与离线 ZIP 生成脚本
- 增加 GUI 打包环境下的 `faulthandler` 兼容处理
- 在缺少 `torch` 时自动禁用 `SRCNN`
- 将网格实时预览和最终应用迁移到后台线程
- 将右侧面板按钮组改为更适合低分辨率的纵向堆叠布局

### 当前仍然偏重的模块

- `ui/main_window.py`

当前仍然承担：

- 图片工作台的大部分面板构建
- 大量 UI 事件连接
- 文本图层交互逻辑

后续建议继续拆分为：

- `ui/panels/text_panel.py`
- `ui/panels/transform_panel.py`
- `ui/panels/mesh_panel.py`

## 7. 维护建议

### 7.1 新增功能时的放置原则

- 纯算法或图像处理逻辑：优先放 `core/` 或 `utils/`
- 文档、PDF、OCR、批处理执行器：优先放 `core/document_tasks.py`，UI 只负责组装任务和展示状态
- 用户配置：优先放 `core/app_settings.py`，设置页只负责交互
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
- `ui/warp_support.py`

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

### 7.6 修改文档工作台时

优先查看：

- `ui/document_workbench.py`
- `core/document_tasks.py`
- `core/app_settings.py`
- `ui/region_picker_dialog.py`

## 8. 常见问题定位

### 导出预览失败

优先检查：

- 模型文件路径是否有效
- 模型名与倍率是否和 `.pb` 文件一致
- OpenCV 是否包含 `dnn_superres`

### 应用启动提示 PyQt / PySide 冲突

优先检查：

- 当前环境是否同时安装了 `PyQt-Fluent-Widgets` 和 `PySide6-Fluent-Widgets`
- `qfluentwidgets.__doc__` 是否显示 PyQt5 版本
- 是否在干净虚拟环境中按 `requirements.txt` 重新安装了依赖

### 导出很慢

优先判断：

- 是否使用了超分模型
- 是否是大图
- 是否在导出而不是预览

### 网格操作卡顿

优先检查：

- `ui/warp_support.py` 是否仍在后台线程执行
- `MeshWarpController._profile()` 的 preview 参数是否被调得过重
- 当前是否在最终应用高质量网格变形，而不是只看预览

### 右侧面板拥挤

优先修改：

- `main_window.py` 的面板布局
- `export_mixin.py` 的按钮编排方式
- 是否能继续拆成子面板模块

### Windows 打包失败

优先检查：

- 当前终端里 `py` 或 `python` 是否真的可调用
- `requirements-windows-build.txt` 是否仍然包含 `requirements.txt` 和打包所需额外项
- 是否误把离线 ZIP 当作仓库源码直接在压缩包内部运行而未完整解压

### 文档任务执行失败

优先检查：

- 设置页和文档工作台中对应后端是否已检测到
- 文件后缀与当前模块目标动作是否匹配
- PDF 加解密任务是否提供了正确口令
- 输出目录是否存在写入权限

## 9. 后续重构建议

建议按以下顺序继续演进：

1. 拆分 `main_window.py` 中各面板构建代码
2. 抽离导出预览缓存为独立 helper
3. 给 `core/` 增加更明确的类型定义
4. 为导出增强和控制器补最小自动化测试
