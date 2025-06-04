import mcp.types as types
from mcp.server.fastmcp import FastMCP
from pydantic import AnyUrl
import json
import asyncio
from typing import Dict, List, Any

# read_resources 获取服务pod ip
# read_resources 获取pod pprof 信息
# read_resources 获取服务metrics
mcp = FastMCP("svc_problem_analysis")


async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri=AnyUrl("/svc/pods_ip/{namespace}/{service_name}"),
            name="svc_pods_ip",
            kind="svc_pods_ip",
            description="获取服务的多个pod ip",
        ),
        # types.Resource(
        #     uri=AnyUrl("/pod/pprof/{namespace}/{pod_name}"),
        #     name="pod_pprof",
        #     kind="pod_pprof",
        #     description="获取pod的pprof信息",
        # ),
        # types.Resource(
        #     uri=AnyUrl("/svc/metrics/{namespace}/{service_name}"),
        #     name="svc_metrics",
        #     kind="svc_metrics",
        #     description="获取服务的metrics信息",
        # )
    ]


async def run_kubectl_command(cmd: List[str]) -> Dict[str, Any]:
    """执行kubectl命令并返回结果"""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return {
                "success": False,
                "error": stderr.decode('utf-8'),
                "returncode": process.returncode
            }

        return {
            "success": True,
            "data": stdout.decode('utf-8'),
            "returncode": process.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "returncode": -1
        }


# @mcp.read_resource()
async def get_svc_pods_ip(namespace: str, service_name: str) -> types.ReadResourceResult:
    """获取服务对应的所有pod IP地址"""

    # 首先获取service对应的selector
    svc_cmd = [
        "kubectl", "get", "pod", service_name,
        "-n", namespace,
        "-o", "json"
    ]

    svc_result = await run_kubectl_command(svc_cmd)
    if not svc_result["success"]:
        return {
            "error": f"获取service信息失败: {svc_result['error']}",
            "service_name": service_name,
            "namespace": namespace
        }

    try:
        svc_data = json.loads(svc_result["data"])
        selector = svc_data.get("spec", {}).get("selector", {})

        if not selector:
            return {
                "error": "Service没有selector",
                "service_name": service_name,
                "namespace": namespace
            }

        # 构建selector字符串
        selector_str = ",".join([f"{k}={v}" for k, v in selector.items()])

        # 获取匹配的pods
        pods_cmd = [
            "kubectl", "get", "pods",
            "-n", namespace,
            "-l", selector_str,
            "-o", "json"
        ]

        pods_result = await run_kubectl_command(pods_cmd)
        if not pods_result["success"]:
            return {
                "error": f"获取pods信息失败: {pods_result['error']}",
                "service_name": service_name,
                "namespace": namespace
            }

        pods_data = json.loads(pods_result["data"])
        pod_ips = []

        for pod in pods_data.get("items", []):
            pod_name = pod.get("metadata", {}).get("name", "")
            pod_ip = pod.get("status", {}).get("podIP", "")
            pod_status = pod.get("status", {}).get("phase", "")

            if pod_ip:
                pod_ips.append({
                    "name": pod_name,
                    "ip": pod_ip,
                    "status": pod_status
                })

        return {
            "service_name": service_name,
            "namespace": namespace,
            "selector": selector,
            "pods": pod_ips,
            "total_pods": len(pod_ips)
        }

    except json.JSONDecodeError as e:
        return {
            "error": f"解析JSON失败: {str(e)}",
            "service_name": service_name,
            "namespace": namespace
        }


async def get_pod_pprof_info(namespace: str, pod_name: str, port: int = 6060):
    """获取pod的pprof信息"""
    pass


async def get_svc_metrics(namespace: str, service_name: str, metrics_port: int = 8080):
    """获取服务的metrics信息"""
    pass

if __name__ == "__main__":
    rsp = asyncio.run(get_svc_pods_ip("im", "user-recommender"))
    print(rsp)
