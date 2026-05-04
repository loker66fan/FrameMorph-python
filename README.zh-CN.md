# FrameMorph-python

基于 `PySide6`、`Pillow` 和 `OpenCV` 构建的桌面图像编辑工具。

`FrameMorph-python` 是项目名称，“形绘”是面向用户展示的软件名称。

它面向本地实用图像处理工作流，当前提供：

- 自由裁剪和比例裁剪
- 缩放、拉伸、旋转
- 网格变形
- 透视矫正
- 文字图层
- 高清导出
- 多种增强路径，包括 OpenCV `dnn_superres`

## 功能特性

- 支持拖拽导入图片
- 画布常驻，右侧面板切换控制功能
- 支持撤销 / 重做
- 网格变形与透视变换支持实时预览
- 导出前后增强预览
- 导出支持后台进度、预计剩余时间和取消
- 支持 OpenCV 超分模型下载与本地模型使用

## 技术栈

- Python 3.11+
- PySide6
- Pillow
- OpenCV
- NumPy

## 项目结构

```text
FrameMorph-python/
├── main.py
├── core/
├── ui/
│   ├── main_window.py
│   ├── export_mixin.py
│   ├── export_support.py
│   └── transform_view.py
├── utils/
├── docs/
│   ├── TECHNICAL.md
│   ├── USER_GUIDE.md
│   └── RELEASE.md
├── assets/
│   └── screenshots/
├── models/
│   └── opencv_dnn_superres/
├── VERSION
├── CHANGELOG.md
├── PROJECT_SUMMARY.md
└── requirements.txt
```

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 超分导出支持

当前导出增强支持三种路径：

1. 内置经典超分增强
2. 使用自定义本地模型路径的 PyTorch SRCNN
3. OpenCV `dnn_superres`
   - EDSR
   - ESPCN
   - FSRCNN
   - LapSRN

应用支持：

- 从 `.pb` 文件名自动识别模型类型和倍率
- 将支持的 OpenCV 模型下载到 `models/opencv_dnn_superres/`
- 导出时显示百分比和预计剩余时间

## 文档

- 技术维护文档：[docs/TECHNICAL.md](docs/TECHNICAL.md)
- 使用文档：[docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- 发布元信息文档：[docs/RELEASE.md](docs/RELEASE.md)
- 中文发布说明：[docs/RELEASE.zh-CN.md](docs/RELEASE.zh-CN.md)
- 打包说明：[docs/PACKAGING.md](docs/PACKAGING.md)
- GitHub Actions Windows 自动构建：[docs/GITHUB_ACTIONS_WINDOWS_BUILD.md](docs/GITHUB_ACTIONS_WINDOWS_BUILD.md)
- 项目简介：[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- 变更记录：[CHANGELOG.md](CHANGELOG.md)
- Windows 便携版构建目录：[release/windows-portable](release/windows-portable)

## 截图

### 工作台

![Workbench](assets/screenshots/workbench.png)

### 网格变形

![Mesh Warp](assets/screenshots/mesh-warp.png)

### 导出面板

![Export Panel](assets/screenshots/export-panel.png)

## 版本

当前版本：`0.1.0`

详见 [VERSION](VERSION)。

## 许可证

MIT License，详见 [LICENSE](LICENSE)。
