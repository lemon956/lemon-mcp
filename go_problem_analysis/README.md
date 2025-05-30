# Go Problem Analysis MCP Server

这是一个通过 pprof 分析 Kubernetes pod 的 profile 和 heap 信息的 MCP server。

## 功能特性

- 🔍 **CPU Profile 分析**: 分析指定 pod 的 CPU 使用情况
- 💾 **堆内存分析**: 分析 pod 的内存分配和使用
- 🔄 **Goroutine 分析**: 查看 goroutine 状态和数量
- 📊 **火焰图生成**: 生成可视化性能分析图表
- 📋 **Pod 状态监控**: 获取 pod 基本状态信息

## 前置要求

1. **Go 工具链**: 需要安装 Go 开发环境，用于 `go tool pprof` 命令
2. **kubectl**: 需要配置好的 kubectl 工具，能够访问 Kubernetes 集群
3. **Python 3.8+**: 运行 MCP server
4. **目标 Pod**: 目标 Go 应用需要启用 pprof 接口（通常在 `:6060/debug/pprof`）

## 安装

1. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

2. 确保您的 Go 应用已启用 pprof：
```go
import _ "net/http/pprof"

func main() {
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()
    // 您的应用代码
}
```

## 使用方法

### 启动 MCP Server

```bash
python main.py
```

### 可用工具

#### 1. analyze_pod_cpu
分析指定 pod 的 CPU profile
```json
{
  "namespace": "default",
  "pod_name": "my-go-app-pod",
  "duration": 30,
  "local_port": 6060
}
```

#### 2. analyze_pod_heap
分析指定 pod 的堆内存使用
```json
{
  "namespace": "default", 
  "pod_name": "my-go-app-pod",
  "local_port": 6060
}
```

#### 3. analyze_pod_goroutines
分析指定 pod 的 goroutine 状态
```json
{
  "namespace": "default",
  "pod_name": "my-go-app-pod",
  "local_port": 6060
}
```

#### 4. get_pod_status
获取 pod 的基本状态信息
```json
{
  "namespace": "default",
  "pod_name": "my-go-app-pod"
}
```

#### 5. generate_flame_graph
生成火焰图分析
```json
{
  "namespace": "default",
  "pod_name": "my-go-app-pod",
  "profile_type": "cpu",
  "duration": 30
}
```

## 工作原理

1. **端口转发**: 使用 `kubectl port-forward` 建立与目标 pod 的连接
2. **数据收集**: 通过 HTTP 请求下载 pprof 数据
3. **数据分析**: 使用 `go tool pprof` 分析性能数据
4. **结果展示**: 将分析结果格式化为易读的报告

## 支持的 Profile 类型

- `cpu`: CPU 使用分析
- `heap`: 堆内存分析  
- `goroutine`: Goroutine 状态分析
- `mutex`: 互斥锁竞争分析
- `block`: 阻塞操作分析
- `allocs`: 内存分配分析
- `threadcreate`: 线程创建分析

## 注意事项

1. 确保目标 pod 中的 Go 应用已启用 pprof 接口
2. 确保有足够的权限执行 `kubectl port-forward`
3. CPU profiling 会有一定的性能开销，建议在生产环境中谨慎使用
4. 生成的 profile 文件和分析结果会保存在临时目录中

## 故障排除

### 连接问题
- 检查 kubectl 配置是否正确
- 确认 pod 名称和 namespace 正确
- 验证 pod 中的应用是否启用了 pprof

### pprof 工具问题
- 确保已安装 Go 工具链
- 检查 `go tool pprof` 命令是否可用

### 权限问题
- 确保有访问 Kubernetes 集群的权限
- 验证是否有执行 port-forward 的权限

## 示例

分析一个名为 `my-app` 的 pod 的 CPU 使用情况：

```bash
# 启动 MCP server 后，调用工具
{
  "name": "analyze_pod_cpu",
  "arguments": {
    "namespace": "production",
    "pod_name": "my-app-7d4b8c9f85-abc123",
    "duration": 60
  }
}
```

这将生成包含 Top CPU 消耗函数的详细报告。 