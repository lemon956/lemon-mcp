#!/bin/bash

# Go Problem Analysis MCP Server 启动脚本

echo "🚀 启动 Go Problem Analysis MCP Server..."

# 检查依赖
echo "📋 检查依赖..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未找到，请先安装 Python 3.8+"
    exit 1
fi

# 检查 kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl 未找到，请先安装和配置 kubectl"
    exit 1
fi

# 检查 Go
if ! command -v go &> /dev/null; then
    echo "❌ Go 未找到，请先安装 Go 工具链"
    exit 1
fi

echo "✅ 所有依赖检查通过"

# Python 环境管理
echo "📦 配置 Python 环境..."

# 检查是否已经在 conda 环境中
if [[ "$CONDA_DEFAULT_ENV" ]]; then
    echo "✅ 已在 conda 环境: $CONDA_DEFAULT_ENV"
fi

# 激活 mcp 环境
source activate mcp
echo "✅ 已激活 mcp 环境: $CONDA_DEFAULT_ENV"

# 显示当前 Python 信息
echo "🐍 Python 信息:"
echo "   路径: $(which python3)"
echo "   版本: $(python3 --version)"

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
python3 -m pip install -r requirements.txt

# 启动服务器
echo "🌟 启动 MCP Server..."
python3 main.py 