import docker
import os
import time
from typing import Optional

def get_client() -> Optional[docker.DockerClient]:
    try:
        return docker.from_env()
    except Exception:
        return None

def _cpu_count(cpu_stats: dict) -> int:
    """
    Number of CPUs available to the container.
    cgroup v2 (Pi OS Bookworm, modern Docker) exposes online_cpus.
    cgroup v1 exposes percpu_usage. Fall back to host core count.
    """
    online = cpu_stats.get("online_cpus")
    if online:
        return online
    percpu = cpu_stats.get("cpu_usage", {}).get("percpu_usage")
    if percpu:
        return len(percpu)
    return os.cpu_count() or 1

def _calc_cpu(raw: dict) -> Optional[float]:
    """Returns CPU percent, or None if the counters arent available."""
    try:
        cpu_stats = raw.get("cpu_stats", {})
        precpu_stats = raw.get("precpu_stats", {})

        total = cpu_stats.get("cpu_usage", {}).get("total_usage")
        pre_total = precpu_stats.get("cpu_usage", {}).get("total_usage")
        system = cpu_stats.get("system_cpu_usage")
        pre_system = precpu_stats.get("system_cpu_usage")

        # any of these missing means we cant compute a delta
        if total is None or pre_total is None or system is None or pre_system is None:
            return None

        cpu_delta = total - pre_total
        sys_delta = system - pre_system

        if sys_delta <= 0 or cpu_delta < 0:
            return None

        num_cpus = _cpu_count(cpu_stats)
        return round((cpu_delta / sys_delta) * num_cpus * 100, 2)
    except Exception:
        return None

def _calc_mem(raw: dict) -> dict:
    """Returns memory dict. Handles cgroup v1, cgroup v2, and ungatherable stats."""
    try:
        mem_block = raw.get("memory_stats", {})
        inner = mem_block.get("stats", {})
        usage = mem_block.get("usage", 0)
        limit = mem_block.get("limit", 0)

        import os
        host_mem = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")

        # cgroup v2 without limit -- try anon as working set
        if not usage and not limit:
            anon = inner.get("anon", 0)
            if not anon:
                # memory cgroup not delegated to Docker on this system
                # report honestly rather than showing 0.0
                return {"mem_usage_mb": None, "mem_note": "memory cgroup not available"}
            cache = inner.get("inactive_file", 0)
            real = max(anon - cache, 0)
            return {
                "mem_usage_mb": round(real / 1024 / 1024, 1),
                "mem_limit_mb": round(host_mem / 1024 / 1024, 1),
                "mem_pct": round((real / host_mem) * 100, 2),
            }

        # cgroup v1 or cgroup v2 with explicit limit
        effective_limit = limit if limit and limit < host_mem else host_mem
        cache = inner.get("inactive_file") or inner.get("cache", 0)
        real = max(usage - cache, 0)
        return {
            "mem_usage_mb": round(real / 1024 / 1024, 1),
            "mem_limit_mb": round(effective_limit / 1024 / 1024, 1),
            "mem_pct": round((real / effective_limit) * 100, 2),
        }
    except Exception as e:
        return {"mem_note": f"mem calc error: {type(e).__name__}: {e}"}

def get_containers() -> list:
    client = get_client()
    if not client:
        return []

    containers = []
    for c in client.containers.list(all=True):
        stats = {}

        if c.status == "running":
            try:
                # prime the delta counter, then take the real sample
                c.stats(stream=False)
                time.sleep(1.5)
                raw = c.stats(stream=False)

                cpu = _calc_cpu(raw)
                if cpu is not None:
                    stats["cpu_pct"] = cpu
                else:
                    stats["cpu_pct"] = "unavailable"

                mem = _calc_mem(raw)
                stats.update(mem)

            except Exception as e:
                # surface the reason instead of silently returning nothing
                stats = {"error": f"stats unavailable: {type(e).__name__}"}

        containers.append({
            "id": c.short_id,
            "name": c.name,
            "image": c.image.tags[0] if c.image.tags else "unknown",
            "status": c.status,
            "stats": stats,
        })
    return containers

def get_container_logs(name: str, lines: int = 50) -> str:
    client = get_client()
    if not client:
        return "Docker unavailable"
    try:
        c = client.containers.get(name)
        return c.logs(tail=lines).decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error: {e}"

def get_summary() -> dict:
    containers = get_containers()
    running = [c for c in containers if c["status"] == "running"]
    stopped = [c for c in containers if c["status"] != "running"]
    return {
        "total": len(containers),
        "running": len(running),
        "stopped": len(stopped),
        "containers": containers,
    }
