# 静态资源说明

本目录包含 3.5 模块所需的所有静态资源,确保 CDN-Free 运行。

## 📁 目录结构

```
static/
├── reveal.js/          # Reveal.js 幻灯片框架
│   └── reveal.js-4.6.1/
│       ├── dist/       # 核心文件 (reveal.js, reveal.css)
│       ├── css/        # 主题样式
│       └── plugin/     # 插件
├── fonts/              # 字体配置
│   └── fonts.css       # 系统字体栈配置
└── icons/              # SVG 图标
    ├── warning.svg     # 警告图标
    ├── tool.svg        # 工具图标
    └── image.svg       # 图片占位符图标
```

## 📦 资源详情

### 1. Reveal.js (v4.6.1)
- **来源**: https://github.com/hakimel/reveal.js/releases/tag/4.6.1
- **大小**: ~2.5 MB
- **用途**: HTML 幻灯片展示框架
- **关键文件**:
  - `dist/reveal.js` - 核心 JS
  - `dist/reveal.css` - 核心样式
  - `dist/theme/` - 内置主题

### 2. 字体配置
- **策略**: 使用系统字体栈,无需下载字体文件
- **中文字体优先级**:
  1. PingFang SC (macOS)
  2. Microsoft YaHei (Windows)
  3. Noto Sans CJK SC (Linux)
  4. Source Han Sans CN (思源黑体)
- **优势**: 零下载,快速加载,良好兼容性

### 3. SVG 图标
- **来源**: Feather Icons (MIT License)
- **格式**: SVG (矢量,可缩放)
- **用途**: 
  - `warning.svg` - 安全警示页面
  - `tool.svg` - 工具设备展示
  - `image.svg` - 图片占位符

## 🔧 使用方式

### 在 Jinja2 模板中引用

```html
<!-- Reveal.js -->
<link rel="stylesheet" href="./static/reveal.js/reveal.js-4.6.1/dist/reveal.css">
<script src="./static/reveal.js/reveal.js-4.6.1/dist/reveal.js"></script>

<!-- 字体 -->
<link rel="stylesheet" href="./static/fonts/fonts.css">

<!-- 图标 -->
<img src="./static/icons/warning.svg" alt="警告" class="icon">
```

## ⚠️ 注意事项

1. **路径**: 所有路径使用相对路径,确保部署灵活性
2. **版本锁定**: Reveal.js 版本固定为 4.6.1,避免 API 变化
3. **离线可用**: 所有资源本地化,无需网络连接
4. **导出友好**: 配置适合 PPTX 导出 (Module 3.7)

## 📝 更新日志

- 2026-01-15: 初始化静态资源
  - 下载 Reveal.js 4.6.1
  - 配置系统字体栈
  - 添加基础 SVG 图标
