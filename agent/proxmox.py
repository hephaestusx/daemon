import requests
import urllib3
urllib3.disable_warnings()

class ProxmoxAgent:
    def __init__(self, config: dict):
        self.host = config.get("host")
        self.user = config.get("user")
        self.token_name = config.get("token_name")
        self.token_value = config.get("token_value")
        self.verify_ssl = config.get("verify_ssl", False)
        self.base = f"https://{self.host}:8006/api2/json"
        self.headers = {
            "Authorization": f"PVEAPIToken={self.user}!{self.token_name}={self.token_value}"
        }

    def _get(self, path: str) -> dict:
        try:
            r = requests.get(
                f"{self.base}{path}",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=5
            )
            return r.json().get("data", {})
        except Exception as e:
            return {"error": str(e)}

    def get_nodes(self) -> list:
        return self._get("/nodes") or []

    def get_vms(self) -> list:
        nodes = self.get_nodes()
        vms = []
        for node in nodes:
            if isinstance(node, dict) and "node" in node:
                result = self._get(f"/nodes/{node['node']}/qemu")
                if isinstance(result, list):
                    for vm in result:
                        vm["node"] = node["node"]
                        vms.append(vm)
        return vms

    def get_node_status(self) -> list:
        nodes = self.get_nodes()
        statuses = []
        for node in nodes:
            if isinstance(node, dict) and "node" in node:
                status = self._get(f"/nodes/{node['node']}/status")
                if isinstance(status, dict):
                    status["node"] = node["node"]
                    statuses.append(status)
        return statuses

    def get_summary(self) -> dict:
        vms = self.get_vms()
        running = [v for v in vms if isinstance(v, dict) and v.get("status") == "running"]
        return {
            "vms_total": len(vms),
            "vms_running": len(running),
            "vms_stopped": len(vms) - len(running),
            "vms": vms,
        }
