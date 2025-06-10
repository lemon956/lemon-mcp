import mcp.types as types
from mcp.server.fastmcp import FastMCP
# from mcp.server.fastmcp.resources.base import Resource
# from mcp.server.stdio import stdio_server
from pydantic import AnyUrl
import json
import asyncio
from typing import Dict, Any
from kubernetes import client
import base64
import tempfile
import yaml
import os
import requests
# import time
import uuid
import subprocess
# import anyio

# read_resources 获取服务pod ip
# read_resources 获取pod pprof 信息
# read_resources 获取服务metrics
mcp = FastMCP(
    name="go-problem-analysis",
    version="1.0.0",
    description="Go应用性能问题分析工具"
)


kube_config_path = "~/.kube/config"


def setup_ssl_from_kubeconfig() -> client.CoreV1Api:
    """从kubeconfig提取证书并设置SSL"""
    try:
        kubeconfig_path = os.path.expanduser(kube_config_path)

        # 添加路径检查
        if not os.path.exists(kubeconfig_path):
            print(f"警告: kubeconfig文件不存在: {kubeconfig_path}")
            return None

        with open(kubeconfig_path, 'r') as f:
            kubeconfig = yaml.safe_load(f)

        # 获取当前context的集群信息
        current_context = kubeconfig.get('current-context')
        contexts = {ctx['name']: ctx['context']
                    for ctx in kubeconfig.get('contexts', [])}
        clusters = {cluster['name']: cluster['cluster']
                    for cluster in kubeconfig.get('clusters', [])}
        users = {user['name']: user['user']
                 for user in kubeconfig.get('users', [])}

        if current_context not in contexts:
            raise ValueError(f"当前context '{current_context}' 未找到")

        context = contexts[current_context]
        cluster = clusters[context['cluster']]
        user = users[context['user']]
        # print("current_context", current_context)
        # print("context", context)
        # print("cluster", cluster)
        # print("user", user)
        configuration = client.Configuration()
        configuration.host = cluster['server']

        # 处理CA证书
        if 'certificate-authority-data' in cluster:
            ca_cert_data = base64.b64decode(
                cluster['certificate-authority-data'])
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.crt') as ca_file:
                ca_file.write(ca_cert_data)
                configuration.ssl_ca_cert = ca_file.name
        elif 'certificate-authority' in cluster:
            configuration.ssl_ca_cert = cluster['certificate-authority']

        # 处理客户端证书
        if 'client-certificate-data' in user:
            client_cert_data = base64.b64decode(
                user['client-certificate-data'])
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.crt') as cert_file:
                cert_file.write(client_cert_data)
                configuration.cert_file = cert_file.name
        elif 'client-certificate' in user:
            configuration.cert_file = user['client-certificate']

        # 处理客户端密钥
        if 'client-key-data' in user:
            client_key_data = base64.b64decode(user['client-key-data'])
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.key') as key_file:
                key_file.write(client_key_data)
                configuration.key_file = key_file.name
        elif 'client-key' in user:
            configuration.key_file = user['client-key']

        # 处理token认证
        # if 'token' in user:
        #     configuration.api_key = {
        #         "authorization": f"Bearer {user['token']}"}

        configuration.verify_ssl = False
        client.Configuration.set_default(configuration)

        return client.CoreV1Api()

    except Exception as e:
        print(f"从kubeconfig设置SSL失败: {e}")
        # 添加更详细的错误信息
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return None


def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri=AnyUrl(
                "resource://pod/pprof/{namespace}/{service_name}"),
            name="load_pod_pprof",
            kind="load_pod_pprof",
            description="""
            获取pod的pprof信息
            @Params:
            - namespace: 命名空间
            - service_name: 服务名称
            @Example:
            - /pod/pprof/im/user-recommender
            """,
            mime_type="text/plain",
        ),
        types.Resource(
            uri=AnyUrl(
                "resource://pod/pprof/{namespace}/{service_name}/{uuid}/{analysis_types}"),
            name="get_pod_analysis_info",
            kind="get_pod_analysis_info",
            description="""
                获取pod的heap信息
                @Params:
                - namespace: 命名空间
                - service_name: 服务名称
                - uuid: 唯一标识
                - analysis_types: 分析类型, 该参数为 go tool pprof 的参数,每一次分析参数为一条值, 多条使用 | 分隔
                @Example:
                - /pod/pprof/im/user-recommender/123e4567-e89b-12d3-a456-426614174000/profile
                """,
            mime_type="text/plain",
        )
    ]


@mcp.resource(uri="resource://pod/pprof/{namespace}/{service_name}")
async def load_pod_pprof(namespace: str, service_name: str) -> types.ReadResourceResult:
    ip_list = await get_svc_pods_ip(namespace, service_name)
    data = []
    for ip in ip_list:
        profile_url = f"http://{ip}:8080/debug/pprof/profile?seconds=30"
        heap_url = f"http://{ip}:8080/debug/pprof/heap?seconds=30"
        profile_response = requests.get(profile_url, timeout=60)
        heap_response = requests.get(heap_url, timeout=60)
        # print(response.text)
        # save load pprof file or heap file, file name with service name, ip, profile or heap, time, uuid  suffix is pb.gz
        # save file to /tmp/pprof/service_name/ip/profile_time_uuid.pb.gz
        base_path = f"/tmp/pprof/{namespace}/{service_name}"
        os.makedirs(base_path, exist_ok=True)
        curr_uuid = str(uuid.uuid4())
        with open(f"{base_path}/profile_{curr_uuid}.pb.gz", "wb") as f:
            f.write(profile_response.content)
        with open(f"{base_path}/heap_{curr_uuid}.pb.gz", "wb") as f:
            f.write(heap_response.content)
        data.append({
            "ip": ip,
            "namespace": namespace,
            "service_name": service_name,
            "profile_uuid": curr_uuid,
        })
    return types.ReadResourceResult(
        contents=[types.TextResourceContents(uri=AnyUrl(
            "resource://pod/pprof/{namespace}/{service_name}"), text=json.dumps(data, ensure_ascii=False))]
    )


async def get_svc_pods_ip(namespace: str, service_name: str) -> list[str]:
    """获取服务对应的所有pod IP地址"""
    pods = kube_cli.list_namespaced_pod(namespace)
    pod_ip_list = []
    for pod in pods.items:
        if pod.metadata.labels.get("app", "") == service_name:
            pod_ip_list.append(pod.status.pod_ip)
            # break
    return pod_ip_list


def execute_go_tool_pprof_sync(cmd: str) -> Dict[str, Any]:
    """同步版本的go tool pprof执行"""
    try:
        # 使用subprocess.run执行命令
        result = subprocess.run(
            cmd.split(" "),
            capture_output=True,
            text=True,
            timeout=30,  # 30秒超时
            cwd="/"
        )

        return {
            "success": result.returncode == 0,
            "command": cmd,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "command": cmd if 'cmd' in locals() else "unknown",
            "error": "命令执行超时",
            "stdout": "",
            "stderr": "",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "command": cmd if 'cmd' in locals() else "unknown",
            "error": str(e),
            "stdout": "",
            "stderr": "",
            "returncode": -1
        }


@mcp.resource(uri="resource://pod/pprof/{namespace}/{service_name}/{uuid}/{analysis_types}")
async def get_pod_analysis_info(namespace: str, service_name: str, uuid: str, analysis_types: str) -> types.ReadResourceResult:
    """获取pod的pprof信息"""
    profile_file_path = f"/tmp/pprof/{namespace}/{service_name}/profile_{uuid}.pb.gz"
    heap_file_path = f"/tmp/pprof/{namespace}/{service_name}/heap_{uuid}.pb.gz"
    print(profile_file_path, "\n", heap_file_path)
    if not os.path.exists(profile_file_path) and not os.path.exists(heap_file_path):
        return types.ReadResourceResult(
            contents=[types.TextResourceContents(uri=AnyUrl(
                "/pod/pprof/{namespace}/{service_name}/{uuid}/{pprof_type}"), text=f"文件不存在: {profile_file_path} 和 {heap_file_path}")]
        )
    analysis_types = analysis_types.split("|")
    data = []
    if os.path.exists(profile_file_path):
        for analysis_type in analysis_types:
            if not analysis_type.startswith('-'):
                analysis_type = f"-{analysis_type}"
            cmd = f"go tool pprof {analysis_type} {profile_file_path}"
            result = execute_go_tool_pprof_sync(
                cmd)
            data.append({
                "pprof_type": "profile",
                "analysis_type": analysis_type,
                "analysis_result": result,
            })
    if os.path.exists(heap_file_path):
        for analysis_type in analysis_types:
            if not analysis_type.startswith('-'):
                analysis_type = f"-{analysis_type}"
            cmd = f"go tool pprof {analysis_type} {heap_file_path}"
            result = execute_go_tool_pprof_sync(cmd)
            data.append({
                "pprof_type": "heap",
                "analysis_type": analysis_type,
                "analysis_result": result,
            })
    return types.ReadResourceResult(
        contents=[types.TextResourceContents(uri=AnyUrl(
            "resource://pod/pprof/{namespace}/{service_name}/{uuid}/{analysis_types}"), text=json.dumps(data, ensure_ascii=False))]
    )


async def get_svc_metrics(namespace: str, service_name: str, metrics_port: int = 8080):
    """获取服务的metrics信息"""
    pass


# async def main():
#     async with stdio_server(mcp) as (read_stream, write_stream):
#         await mcp.run(read_stream, write_stream)


kube_cli = setup_ssl_from_kubeconfig()
if kube_cli is None:
    print("警告: Kubernetes客户端初始化失败，某些功能可能不可用")


if __name__ == "__main__":
    try:
        # 注册资源
        resources = list_resources()
        for resource in resources:
            mcp.add_resource(resource)

        print(f"已注册 {len(resources)} 个资源")

        # 测试资源列表
        resource_list = asyncio.run(mcp.list_resources())
        print(f"资源列表验证: {len(resource_list)} 个资源")

        # 启动服务器
        print("启动 MCP 服务器...")
        mcp.run(transport="stdio")

    except Exception as e:
        print(f"启动服务器时发生错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
