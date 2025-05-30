# 桌面文件分析器 MCP 服务 - 在 Cursor 中使用

这是一个专门用于分析本地桌面目录文件的 MCP (Model Context Protocol) 服务器，提供强大的文件管理和分析功能。

## 🎯 功能特色

### 📁 桌面文件扫描
- 自动检测桌面目录（支持 Windows、macOS、Linux）
- 递归扫描子目录（可配置深度）
- 支持隐藏文件扫描
- 智能文件分类（图片、文档、视频、音频等）

### 📊 文件分析
- 文件类型分布统计
- 文件大小分析
- 重复文件检测
- 大文件查找
- 文件搜索功能

### 🧹 清理建议
- 桌面整理建议
- 文件分类建议
- 清理优化建议

## 🚀 在 Cursor 中配置使用

### 步骤 1: 测试服务器

首先确保服务器可以正常运行：

```bash
cd /home/hellotalk/selfPorject/mcp/demo
python server.py
```

应该会看到类似这样的日志：
```
INFO:desktop-analyzer-mcp:🚀 启动桌面分析 MCP Server... (桌面路径: /home/user/Desktop)
```

按 `Ctrl+C` 停止服务器。

### 步骤 2: 配置 Cursor

1. 打开 Cursor 编辑器
2. 按 `Cmd/Ctrl + Shift + P` 打开命令面板
3. 搜索 "Preferences: Open Settings (JSON)"
4. 在设置文件中添加 MCP 服务器配置：

```json
{
  "mcpServers": {
    "desktop-analyzer": {
      "command": "python",
      "args": ["/home/hellotalk/selfPorject/mcp/demo/server.py"],
      "env": {
        "PYTHONPATH": "/home/hellotalk/selfPorject/mcp/demo"
      }
    }
  }
}
```

**注意**: 请根据你的实际路径调整配置中的路径。

### 步骤 3: 重启 Cursor

保存配置后，重启 Cursor 以加载 MCP 服务器。

### 步骤 4: 验证配置

1. 在 Cursor 中打开聊天界面
2. 输入类似 `@desktop-analyzer` 的内容查看工具是否可用

## 🛠️ 可用工具和用法

### 1. 桌面扫描 (`scan_desktop`)

扫描桌面目录，获取所有文件信息：

```
请帮我扫描桌面，查看有哪些文件

请扫描桌面，包含隐藏文件，扫描深度为2层
```

### 2. 文件类型分析 (`analyze_file_types`)

分析文件类型分布：

```
请分析桌面文件的类型分布

请按文件扩展名分析文件类型

请按MIME类型分析文件分布
```

### 3. 文件详细信息 (`get_file_details`)

获取特定文件的详细信息：

```
请查看文件 "report.pdf" 的详细信息

请告诉我 "config.txt" 文件的详细属性
```

### 4. 查找大文件 (`find_large_files`)

查找桌面上的大文件：

```
请找出桌面上大于 50MB 的文件

请列出前20个最大的文件
```

### 5. 重复文件检测 (`find_duplicate_files`)

查找可能重复的文件：

```
请检查桌面上是否有重复文件

请查找相似度大于 90% 的重复文件
```

### 6. 清理建议 (`clean_desktop_suggestions`)

生成桌面清理和整理建议：

```
请给我一些桌面整理建议

请生成桌面清理建议

请分析桌面并提供优化建议
```

### 7. 文件搜索 (`search_files`)

在桌面搜索文件：

```
请在桌面搜索包含 "报告" 的文件

请搜索所有图片文件

请搜索 Excel 文档
```

### 8. 桌面统计 (`get_desktop_stats`)

获取桌面的综合统计信息：

```
请显示桌面的统计信息

请生成桌面文件分析报告
```

## 💡 使用场景示例

### 场景 1: 桌面清理

```
我的桌面很乱，请帮我分析一下，然后给出整理建议
```

AI 会：
1. 扫描桌面文件
2. 分析文件类型分布
3. 提供分类整理建议

### 场景 2: 找到大文件

```
我的磁盘空间不够了，请帮我找出桌面上占空间最大的文件
```

AI 会：
1. 扫描桌面
2. 查找大文件
3. 提供删除建议

### 场景 3: 文件搜索

```
我记得桌面上有一个重要的PDF文件，但找不到了，请帮我搜索
```

AI 会：
1. 搜索PDF类型文件
2. 显示匹配结果
3. 提供文件详细信息

### 场景 4: 重复文件清理

```
请检查桌面是否有重复的文件，我想清理一下
```

AI 会：
1. 扫描所有文件
2. 检测重复文件
3. 提供清理建议

## 📊 支持的文件类型

服务器能够识别和分类以下文件类型：

- **图片**: JPG, PNG, GIF, BMP, TIFF, WebP, SVG, ICO
- **文档**: PDF, DOC, DOCX, TXT, RTF, ODT, Pages
- **电子表格**: XLS, XLSX, CSV, ODS, Numbers
- **演示文稿**: PPT, PPTX, ODP, Key
- **视频**: MP4, AVI, MKV, MOV, WMV, FLV, WebM, M4V
- **音频**: MP3, WAV, FLAC, AAC, OGG, WMA, M4A
- **压缩包**: ZIP, RAR, 7Z, TAR, GZ, BZ2, XZ
- **可执行文件**: EXE, MSI, APP, DEB, RPM, DMG
- **代码文件**: PY, JS, HTML, CSS, JAVA, CPP, C, PHP, RB, GO
- **数据文件**: JSON, XML, YAML, SQL, DB, SQLite

## 🔧 高级配置

### 自定义桌面路径

如果你的桌面路径不是标准路径，可以修改 `server.py` 中的 `_get_desktop_path()` 方法。

### 扫描参数调整

- `max_depth`: 扫描深度（1-3层）
- `include_hidden`: 是否包含隐藏文件
- `min_size_mb`: 大文件阈值
- `similarity_threshold`: 重复文件相似度阈值

## 🛡️ 安全说明

1. 服务器只读取文件元数据，不会修改或删除文件
2. 所有操作都限制在桌面目录及其子目录中
3. 敏感信息（如文件内容）不会被读取或传输
4. 只有文件名、大小、时间戳等基本信息会被分析

## 🔍 故障排除

### 问题 1: 桌面路径检测失败

**症状**: 显示 "无法找到桌面目录"

**解决方案**:
- 检查桌面目录是否存在
- 手动修改 `_get_desktop_path()` 方法中的路径

### 问题 2: 权限错误

**症状**: "无法访问某些文件"

**解决方案**:
- 确保 Python 有足够的文件系统访问权限
- 在 Linux/macOS 上可能需要调整文件权限

### 问题 3: MCP 连接失败

**症状**: Cursor 无法连接到 MCP 服务器

**解决方案**:
- 检查配置文件中的路径是否正确
- 确保 Python 可执行文件在 PATH 中
- 重启 Cursor

## 📈 性能优化

- 大型桌面目录（>1000文件）可能需要较长扫描时间
- 建议设置合适的扫描深度以平衡性能和完整性
- 文件缓存机制减少重复扫描的开销

## 🔄 版本历史

- **v1.0.0**: 初始版本，支持基本文件扫描和分析功能

---

现在你可以在 Cursor 中享受强大的桌面文件分析功能了！🎉 