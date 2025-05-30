#!/usr/bin/env python3
"""
Desktop File Analyzer MCP Server - 桌面文件分析 MCP 服务器

这个 MCP 服务器专门用于分析桌面目录中的文件，提供文件类型统计、
文件管理和文件内容分析等功能，专为 Cursor 编辑器优化。
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import mimetypes
import platform

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("desktop-analyzer-mcp")


class DesktopAnalyzerMCPServer:
    """桌面文件分析 MCP 服务器"""

    def __init__(self):
        # 获取桌面路径
        self.desktop_path = self._get_desktop_path()
        self.file_cache = {}
        self.last_scan_time = None

    def _get_desktop_path(self) -> str:
        """获取桌面目录路径"""
        system = platform.system()

        if system == "Windows":
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        elif system == "Darwin":  # macOS
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        else:  # Linux
            # 尝试多个可能的桌面目录
            possible_paths = [
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.join(os.path.expanduser("~"), "桌面"),
                os.path.join(os.path.expanduser("~"), "デスクトップ"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    desktop = path
                    break
            else:
                desktop = os.path.expanduser("~")  # 如果找不到桌面，使用用户主目录

        return desktop

    def get_tools_definition(self):
        """返回可用的工具定义"""
        return [
            {
                "name": "scan_desktop",
                "description": "扫描桌面目录，获取所有文件信息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_hidden": {
                            "type": "boolean",
                            "description": "是否包含隐藏文件",
                            "default": False
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "扫描深度（1=仅桌面，2=包含一级子目录）",
                            "default": 1,
                            "minimum": 1,
                            "maximum": 3
                        }
                    }
                }
            },
            {
                "name": "analyze_file_types",
                "description": "分析桌面文件类型分布",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "group_by": {
                            "type": "string",
                            "description": "分组方式",
                            "enum": ["extension", "mimetype", "category"],
                            "default": "category"
                        }
                    }
                }
            },
            {
                "name": "get_file_details",
                "description": "获取特定文件的详细信息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "文件名（相对于桌面目录）"
                        }
                    },
                    "required": ["filename"]
                }
            },
            {
                "name": "find_large_files",
                "description": "查找桌面上的大文件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "min_size_mb": {
                            "type": "number",
                            "description": "最小文件大小（MB）",
                            "default": 10,
                            "minimum": 0.1
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果数量限制",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        }
                    }
                }
            },
            {
                "name": "find_duplicate_files",
                "description": "查找桌面上可能重复的文件（基于文件名模式）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "similarity_threshold": {
                            "type": "number",
                            "description": "相似度阈值（0-1）",
                            "default": 0.8,
                            "minimum": 0.1,
                            "maximum": 1.0
                        }
                    }
                }
            },
            {
                "name": "clean_desktop_suggestions",
                "description": "生成桌面清理建议",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "analysis_type": {
                            "type": "string",
                            "description": "分析类型",
                            "enum": ["organization", "cleanup", "optimization"],
                            "default": "organization"
                        }
                    }
                }
            },
            {
                "name": "search_files",
                "description": "在桌面搜索文件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        },
                        "file_type": {
                            "type": "string",
                            "description": "文件类型过滤",
                            "enum": ["all", "image", "document", "video", "audio", "archive", "executable"]
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_desktop_stats",
                "description": "获取桌面统计信息",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """处理工具调用"""
        try:
            if name == "scan_desktop":
                return await self._scan_desktop(arguments)
            elif name == "analyze_file_types":
                return await self._analyze_file_types(arguments)
            elif name == "get_file_details":
                return await self._get_file_details(arguments)
            elif name == "find_large_files":
                return await self._find_large_files(arguments)
            elif name == "find_duplicate_files":
                return await self._find_duplicate_files(arguments)
            elif name == "clean_desktop_suggestions":
                return await self._clean_desktop_suggestions(arguments)
            elif name == "search_files":
                return await self._search_files(arguments)
            elif name == "get_desktop_stats":
                return await self._get_desktop_stats(arguments)
            else:
                return {
                    "success": False,
                    "error": f"未知工具: {name}",
                    "content": f"工具 '{name}' 不存在"
                }
        except Exception as e:
            logger.error(f"工具调用错误 {name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"执行工具 '{name}' 时发生错误: {str(e)}"
            }

    def _get_file_category(self, file_path: str) -> str:
        """根据文件扩展名确定文件类别"""
        ext = Path(file_path).suffix.lower()

        categories = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'],
            'spreadsheet': ['.xls', '.xlsx', '.csv', '.ods', '.numbers'],
            'presentation': ['.ppt', '.pptx', '.odp', '.key'],
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            'executable': ['.exe', '.msi', '.app', '.deb', '.rpm', '.dmg'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go'],
            'data': ['.json', '.xml', '.yaml', '.sql', '.db', '.sqlite']
        }

        for category, extensions in categories.items():
            if ext in extensions:
                return category

        return 'other'

    def _scan_directory(self, path: str, max_depth: int, current_depth: int = 1, include_hidden: bool = False) -> List[Dict]:
        """递归扫描目录"""
        files = []

        try:
            for item in os.listdir(path):
                if not include_hidden and item.startswith('.'):
                    continue

                item_path = os.path.join(path, item)

                try:
                    stat = os.stat(item_path)
                    is_dir = os.path.isdir(item_path)

                    file_info = {
                        'name': item,
                        'path': item_path,
                        'relative_path': os.path.relpath(item_path, self.desktop_path),
                        'size': stat.st_size if not is_dir else 0,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'is_directory': is_dir,
                        'depth': current_depth
                    }

                    if not is_dir:
                        file_info['extension'] = Path(item).suffix.lower()
                        file_info['category'] = self._get_file_category(item)
                        file_info['mimetype'] = mimetypes.guess_type(item)[
                            0] or 'unknown'

                    files.append(file_info)

                    # 递归扫描子目录
                    if is_dir and current_depth < max_depth:
                        files.extend(self._scan_directory(
                            item_path, max_depth, current_depth + 1, include_hidden))

                except (OSError, PermissionError) as e:
                    logger.warning(f"无法访问 {item_path}: {e}")
                    continue

        except (OSError, PermissionError) as e:
            logger.error(f"无法读取目录 {path}: {e}")

        return files

    async def _scan_desktop(self, arguments: dict) -> dict:
        """扫描桌面目录"""
        include_hidden = arguments.get("include_hidden", False)
        max_depth = arguments.get("max_depth", 1)

        if not os.path.exists(self.desktop_path):
            return {
                "success": False,
                "error": "桌面目录不存在",
                "content": f"❌ 无法找到桌面目录: {self.desktop_path}"
            }

        files = self._scan_directory(
            self.desktop_path, max_depth, include_hidden=include_hidden)
        self.file_cache = {f['relative_path']: f for f in files}
        self.last_scan_time = datetime.now()

        # 统计信息
        total_files = len([f for f in files if not f['is_directory']])
        total_dirs = len([f for f in files if f['is_directory']])
        total_size = sum(f['size'] for f in files if not f['is_directory'])

        result = f"""📁 桌面扫描完成！
        
🏠 桌面路径: {self.desktop_path}
📊 统计信息:
   • 文件数量: {total_files}
   • 目录数量: {total_dirs}
   • 总大小: {self._format_size(total_size)}
   • 扫描深度: {max_depth}
   • 包含隐藏文件: {'是' if include_hidden else '否'}

📋 前 10 个文件:
"""

        for file in files[:10]:
            if file['is_directory']:
                result += f"   📁 {file['name']}/\n"
            else:
                size_str = self._format_size(file['size'])
                result += f"   📄 {file['name']} ({size_str}) - {file['category']}\n"

        if len(files) > 10:
            result += f"   ... 还有 {len(files) - 10} 个项目"

        return {
            "success": True,
            "content": result
        }

    async def _analyze_file_types(self, arguments: dict) -> dict:
        """分析文件类型分布"""
        group_by = arguments.get("group_by", "category")

        if not self.file_cache:
            return {
                "success": False,
                "error": "请先扫描桌面",
                "content": "❌ 请先使用 scan_desktop 工具扫描桌面"
            }

        files = [f for f in self.file_cache.values() if not f['is_directory']]

        if group_by == "extension":
            groups = {}
            for file in files:
                ext = file.get('extension', '无扩展名')
                if ext not in groups:
                    groups[ext] = {'count': 0, 'size': 0}
                groups[ext]['count'] += 1
                groups[ext]['size'] += file['size']
        elif group_by == "mimetype":
            groups = {}
            for file in files:
                mime = file.get('mimetype', 'unknown')
                if mime not in groups:
                    groups[mime] = {'count': 0, 'size': 0}
                groups[mime]['count'] += 1
                groups[mime]['size'] += file['size']
        else:  # category
            groups = {}
            for file in files:
                cat = file.get('category', 'other')
                if cat not in groups:
                    groups[cat] = {'count': 0, 'size': 0}
                groups[cat]['count'] += 1
                groups[cat]['size'] += file['size']

        # 按文件数量排序
        sorted_groups = sorted(
            groups.items(), key=lambda x: x[1]['count'], reverse=True)

        result = f"📊 文件类型分析 (按 {group_by} 分组):\n\n"

        for group_name, data in sorted_groups:
            percentage = (data['count'] / len(files)) * 100
            result += f"🔸 {group_name}\n"
            result += f"   数量: {data['count']} ({percentage:.1f}%)\n"
            result += f"   大小: {self._format_size(data['size'])}\n\n"

        return {
            "success": True,
            "content": result
        }

    async def _get_file_details(self, arguments: dict) -> dict:
        """获取文件详细信息"""
        filename = arguments["filename"]

        file_path = os.path.join(self.desktop_path, filename)

        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": "文件不存在",
                "content": f"❌ 文件不存在: {filename}"
            }

        try:
            stat = os.stat(file_path)
            path_obj = Path(file_path)

            details = {
                "name": path_obj.name,
                "full_path": file_path,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "is_directory": os.path.isdir(file_path),
                "permissions": oct(stat.st_mode)[-3:],
            }

            if not details["is_directory"]:
                details["extension"] = path_obj.suffix.lower()
                details["category"] = self._get_file_category(file_path)
                details["mimetype"] = mimetypes.guess_type(file_path)[
                    0] or 'unknown'

            result = f"""📄 文件详细信息: {details['name']}

📍 路径: {details['full_path']}
📏 大小: {self._format_size(details['size'])}
📅 创建时间: {details['created']}
📝 修改时间: {details['modified']}
👁️ 访问时间: {details['accessed']}
🔒 权限: {details['permissions']}
📁 类型: {'目录' if details['is_directory'] else '文件'}
"""

            if not details["is_directory"]:
                result += f"""🏷️ 扩展名: {details['extension'] or '无'}
📂 类别: {details['category']}
🎭 MIME类型: {details['mimetype']}"""

            return {
                "success": True,
                "content": result
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": f"❌ 获取文件信息失败: {str(e)}"
            }

    async def _find_large_files(self, arguments: dict) -> dict:
        """查找大文件"""
        min_size_mb = arguments.get("min_size_mb", 10)
        limit = arguments.get("limit", 10)

        if not self.file_cache:
            return {
                "success": False,
                "error": "请先扫描桌面",
                "content": "❌ 请先使用 scan_desktop 工具扫描桌面"
            }

        min_size_bytes = min_size_mb * 1024 * 1024
        large_files = [
            f for f in self.file_cache.values()
            if not f['is_directory'] and f['size'] >= min_size_bytes
        ]

        # 按大小排序
        large_files.sort(key=lambda x: x['size'], reverse=True)
        large_files = large_files[:limit]

        if not large_files:
            return {
                "success": True,
                "content": f"✅ 没有找到大于 {min_size_mb}MB 的文件"
            }

        result = f"🐘 找到 {len(large_files)} 个大文件 (>{min_size_mb}MB):\n\n"

        for i, file in enumerate(large_files, 1):
            result += f"{i}. 📄 {file['name']}\n"
            result += f"   大小: {self._format_size(file['size'])}\n"
            result += f"   类型: {file['category']}\n"
            result += f"   路径: {file['relative_path']}\n\n"

        total_size = sum(f['size'] for f in large_files)
        result += f"💾 总计大小: {self._format_size(total_size)}"

        return {
            "success": True,
            "content": result
        }

    async def _find_duplicate_files(self, arguments: dict) -> dict:
        """查找可能重复的文件"""
        similarity_threshold = arguments.get("similarity_threshold", 0.8)

        if not self.file_cache:
            return {
                "success": False,
                "error": "请先扫描桌面",
                "content": "❌ 请先使用 scan_desktop 工具扫描桌面"
            }

        files = [f for f in self.file_cache.values() if not f['is_directory']]
        duplicates = []

        # 简单的基于文件名相似度的重复检测
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                # 计算文件名相似度（简单的字符匹配）
                name1 = Path(file1['name']).stem.lower()
                name2 = Path(file2['name']).stem.lower()

                if name1 == name2:
                    similarity = 1.0
                else:
                    # 简单的相似度计算
                    common_chars = set(name1) & set(name2)
                    total_chars = set(name1) | set(name2)
                    similarity = len(common_chars) / \
                        len(total_chars) if total_chars else 0

                if similarity >= similarity_threshold:
                    duplicates.append({
                        'file1': file1,
                        'file2': file2,
                        'similarity': similarity
                    })

        if not duplicates:
            return {
                "success": True,
                "content": f"✅ 没有找到相似度大于 {similarity_threshold:.0%} 的重复文件"
            }

        result = f"🔍 找到 {len(duplicates)} 组可能重复的文件:\n\n"

        for i, dup in enumerate(duplicates, 1):
            result += f"{i}. 相似度: {dup['similarity']:.0%}\n"
            result += f"   📄 {dup['file1']['name']} ({self._format_size(dup['file1']['size'])})\n"
            result += f"   📄 {dup['file2']['name']} ({self._format_size(dup['file2']['size'])})\n\n"

        return {
            "success": True,
            "content": result
        }

    async def _clean_desktop_suggestions(self, arguments: dict) -> dict:
        """生成桌面清理建议"""
        analysis_type = arguments.get("analysis_type", "organization")

        if not self.file_cache:
            return {
                "success": False,
                "error": "请先扫描桌面",
                "content": "❌ 请先使用 scan_desktop 工具扫描桌面"
            }

        files = [f for f in self.file_cache.values() if not f['is_directory']]

        if analysis_type == "organization":
            # 按类别分组建议
            categories = {}
            for file in files:
                cat = file['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(file)

            result = "📋 桌面整理建议:\n\n"

            for category, cat_files in categories.items():
                if len(cat_files) > 2:  # 只对有多个文件的类别提供建议
                    result += f"📁 建议创建 '{category}' 文件夹，移入 {len(cat_files)} 个文件:\n"
                    for file in cat_files[:5]:  # 只显示前5个
                        result += f"   • {file['name']}\n"
                    if len(cat_files) > 5:
                        result += f"   ... 还有 {len(cat_files) - 5} 个文件\n"
                    result += "\n"

        elif analysis_type == "cleanup":
            # 清理建议
            large_files = [f for f in files if f['size']
                           > 50 * 1024 * 1024]  # >50MB
            old_files = []

            # 查找旧文件（超过30天未修改）
            now = datetime.now()
            for file in files:
                modified = datetime.fromisoformat(file['modified'])
                if (now - modified).days > 30:
                    old_files.append(file)

            result = "🧹 桌面清理建议:\n\n"

            if large_files:
                result += f"🐘 大文件清理 ({len(large_files)} 个文件):\n"
                for file in large_files[:5]:
                    result += f"   • {file['name']} - {self._format_size(file['size'])}\n"
                result += "\n"

            if old_files:
                result += f"📅 旧文件清理 ({len(old_files)} 个文件):\n"
                for file in old_files[:5]:
                    days_old = (
                        now - datetime.fromisoformat(file['modified'])).days
                    result += f"   • {file['name']} - {days_old} 天前修改\n"
                result += "\n"

        else:  # optimization
            result = "⚡ 桌面优化建议:\n\n"

            total_files = len(files)
            if total_files > 20:
                result += f"📊 桌面文件过多 ({total_files} 个)，建议整理\n\n"

            # 统计各类型文件
            categories = {}
            for file in files:
                cat = file['category']
                categories[cat] = categories.get(cat, 0) + 1

            result += "📈 文件类型分布建议:\n"
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                if count > 3:
                    result += f"   • {cat}: {count} 个文件 - 建议分类整理\n"

        return {
            "success": True,
            "content": result
        }

    async def _search_files(self, arguments: dict) -> dict:
        """搜索文件"""
        query = arguments["query"].lower()
        file_type = arguments.get("file_type", "all")

        if not self.file_cache:
            return {
                "success": False,
                "error": "请先扫描桌面",
                "content": "❌ 请先使用 scan_desktop 工具扫描桌面"
            }

        files = [f for f in self.file_cache.values() if not f['is_directory']]

        # 按文件类型过滤
        if file_type != "all":
            type_mapping = {
                "image": "image",
                "document": ["document", "spreadsheet", "presentation"],
                "video": "video",
                "audio": "audio",
                "archive": "archive",
                "executable": "executable"
            }

            if file_type in type_mapping:
                allowed_categories = type_mapping[file_type]
                if isinstance(allowed_categories, str):
                    allowed_categories = [allowed_categories]
                files = [f for f in files if f['category']
                         in allowed_categories]

        # 搜索匹配
        matches = []
        for file in files:
            if query in file['name'].lower():
                matches.append(file)

        if not matches:
            return {
                "success": True,
                "content": f"🔍 没有找到包含 '{query}' 的文件"
            }

        result = f"🔍 搜索 '{query}' 找到 {len(matches)} 个文件:\n\n"

        for i, file in enumerate(matches[:20], 1):  # 限制显示20个结果
            result += f"{i}. 📄 {file['name']}\n"
            result += f"   大小: {self._format_size(file['size'])}\n"
            result += f"   类型: {file['category']}\n"
            result += f"   路径: {file['relative_path']}\n\n"

        if len(matches) > 20:
            result += f"... 还有 {len(matches) - 20} 个匹配文件"

        return {
            "success": True,
            "content": result
        }

    async def _get_desktop_stats(self, arguments: dict) -> dict:
        """获取桌面统计信息"""
        if not self.file_cache:
            return {
                "success": False,
                "error": "请先扫描桌面",
                "content": "❌ 请先使用 scan_desktop 工具扫描桌面"
            }

        files = [f for f in self.file_cache.values() if not f['is_directory']]
        dirs = [f for f in self.file_cache.values() if f['is_directory']]

        # 基本统计
        total_files = len(files)
        total_dirs = len(dirs)
        total_size = sum(f['size'] for f in files)

        # 类别统计
        categories = {}
        for file in files:
            cat = file['category']
            categories[cat] = categories.get(cat, 0) + 1

        # 大小统计
        size_ranges = {
            "< 1KB": 0,
            "1KB - 1MB": 0,
            "1MB - 10MB": 0,
            "10MB - 100MB": 0,
            "> 100MB": 0
        }

        for file in files:
            size = file['size']
            if size < 1024:
                size_ranges["< 1KB"] += 1
            elif size < 1024 * 1024:
                size_ranges["1KB - 1MB"] += 1
            elif size < 10 * 1024 * 1024:
                size_ranges["1MB - 10MB"] += 1
            elif size < 100 * 1024 * 1024:
                size_ranges["10MB - 100MB"] += 1
            else:
                size_ranges["> 100MB"] += 1

        result = f"""📊 桌面统计报告
        
🏠 桌面路径: {self.desktop_path}
📅 最后扫描: {self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_scan_time else '未知'}

📁 基本统计:
   • 文件总数: {total_files}
   • 目录总数: {total_dirs}
   • 总大小: {self._format_size(total_size)}
   • 平均文件大小: {self._format_size(total_size / total_files) if total_files > 0 else '0 B'}

📂 文件类别分布:
"""

        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_files) * 100 if total_files > 0 else 0
            result += f"   • {category}: {count} ({percentage:.1f}%)\n"

        result += "\n📏 文件大小分布:\n"
        for size_range, count in size_ranges.items():
            percentage = (count / total_files) * 100 if total_files > 0 else 0
            result += f"   • {size_range}: {count} ({percentage:.1f}%)\n"

        return {
            "success": True,
            "content": result
        }

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"


# MCP 协议处理
def create_mcp_response(request_id: str, result: Any) -> str:
    """创建 MCP 响应"""
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }
    return json.dumps(response)


def create_mcp_error(request_id: str, code: int, message: str) -> str:
    """创建 MCP 错误响应"""
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message
        }
    }
    return json.dumps(response)


async def handle_mcp_request(server: DesktopAnalyzerMCPServer, request: dict) -> str:
    """处理 MCP 请求"""
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": "desktop-analyzer-mcp",
                    "version": "1.0.0"
                }
            }
            return create_mcp_response(request_id, result)

        elif method == "tools/list":
            tools = server.get_tools_definition()
            result = {"tools": tools}
            return create_mcp_response(request_id, result)

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            tool_result = await server.call_tool(tool_name, arguments)

            result = {
                "content": [
                    {
                        "type": "text",
                        "text": tool_result.get("content", "")
                    }
                ],
                "isError": not tool_result.get("success", False)
            }
            return create_mcp_response(request_id, result)

        else:
            return create_mcp_error(request_id, -32601, f"未知方法: {method}")

    except Exception as e:
        logger.error(f"处理请求时发生错误: {e}")
        return create_mcp_error(request_id, -32603, f"内部错误: {str(e)}")


async def main():
    """主函数 - 启动 stdio MCP 服务器"""
    server = DesktopAnalyzerMCPServer()
    logger.info(f"🚀 启动桌面分析 MCP Server... (桌面路径: {server.desktop_path})")

    try:
        while True:
            # 从标准输入读取请求
            line = sys.stdin.readline()
            if not line:
                break

            try:
                request = json.loads(line.strip())
                logger.info(f"请求: {request}")
                response = await handle_mcp_request(server, request)
                print(response, flush=True)
            except json.JSONDecodeError:
                logger.error(f"无效的 JSON 请求: {line}")
            except Exception as e:
                logger.error(f"处理请求时发生错误: {e}")

    except KeyboardInterrupt:
        logger.info("服务器已停止")


if __name__ == "__main__":
    asyncio.run(main())
