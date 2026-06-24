import re
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
from utils.base import RouterConnector

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class TPLinkConnector(RouterConnector):
    def __init__(self, router):
        super().__init__(router)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json, text/javascript, */*",
            "X-Requested-With": "XMLHttpRequest",
        })
        self.stok = None
        proto = "https" if router.protocol == "https" else "http"
        self.base_url = f"{proto}://{router.ip_address}:{router.port or 80}"
        self.luci_base = None

    def connect(self) -> bool:
        try:
            payload = {
                "username": self.router.username or "admin",
                "password": self.router.password or "admin",
            }
            login_url = f"{self.base_url}/cgi-bin/luci/admin/login"
            resp = self.session.post(
                login_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=15,
                verify=False,
            )

            if resp.status_code in (200, 302):
                try:
                    data = resp.json()
                    self.stok = (
                        data.get("stok")
                        or data.get("data", {}).get("stok")
                        or data.get("result", {}).get("stok")
                    )
                except (json.JSONDecodeError, ValueError):
                    pass

                if not self.stok:
                    self.stok = self._extract_stok_from_text(resp.text)

                if self.stok:
                    self.luci_base = f"{self.base_url}/cgi-bin/luci/;stok={self.stok}/admin"
                    return True

            legacy_payload = {
                "Username": self.router.username or "admin",
                "Password": self.router.password or "admin",
                "Action": "1",
            }
            legacy_resp = self.session.post(
                f"{self.base_url}/userRpm/LoginRpm.htm",
                data=legacy_payload,
                timeout=15,
                verify=False,
            )
            if legacy_resp.status_code == 200:
                self.stok = self._extract_stok_from_text(legacy_resp.text)
                if self.stok:
                    self.luci_base = f"{self.base_url}/userRpm"
                    return True

            self.router.connection_error = "Login failed: invalid credentials or unsupported firmware"
            return False

        except requests.exceptions.ConnectionError:
            self.router.connection_error = "Connection refused. Is the router online?"
            return False
        except requests.exceptions.Timeout:
            self.router.connection_error = "Connection timed out."
            return False
        except Exception as e:
            self.router.connection_error = str(e)
            return False

    def _extract_stok_from_text(self, text: str):
        if not text:
            return None
        m = re.search(r'stok=([a-f0-9]{32,64})', text)
        if m:
            return m.group(1)
        m = re.search(r'"stok"\s*:\s*"([a-f0-9]{32,64})"', text)
        if m:
            return m.group(1)
        return None

    def _api_get(self, endpoint: str, params: dict = None):
        if not self.luci_base:
            raise RuntimeError("Not authenticated. Call connect() first.")
        url = f"{self.luci_base}/{endpoint}"
        return self.session.get(url, params=params, timeout=15, verify=False)

    def _api_post(self, endpoint: str, data: dict = None):
        if not self.luci_base:
            raise RuntimeError("Not authenticated. Call connect() first.")
        url = f"{self.luci_base}/{endpoint}"
        payload = json.dumps(data) if data else None
        return self.session.post(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,
            verify=False,
        )

    def disconnect(self):
        self.session.close()
        self.stok = None
        self.luci_base = None

    def get_system_info(self) -> dict:
        try:
            r = self._api_get("system?form=status")
            if r.status_code == 200:
                try:
                    d = r.json()
                    data = d.get("data", d)
                    return {
                        "name": data.get("name") or data.get("dev_name") or self.router.name,
                        "firmware": data.get("software_version") or data.get("firmware_version", ""),
                        "uptime": data.get("uptime") or data.get("system_time", ""),
                        "model": data.get("model") or data.get("product_name", ""),
                        "cpu_load": data.get("cpu_load", 0),
                    }
                except (json.JSONDecodeError, ValueError):
                    pass

            r2 = self._api_get("system?form=sysmode")
            if r2.status_code == 200:
                try:
                    d = r2.json()
                    data = d.get("data", d)
                    return {
                        "name": data.get("name", self.router.name),
                        "firmware": data.get("software_version", ""),
                        "uptime": data.get("uptime", ""),
                        "model": data.get("model", ""),
                    }
                except (json.JSONDecodeError, ValueError):
                    pass

            return {}
        except Exception as e:
            return {"error": str(e)}

    def get_dhcp_leases(self) -> list:
        try:
            r = self._api_get("network?form=client")
            if r.status_code == 200:
                try:
                    d = r.json()
                    clients = d.get("data", {}).get("client_list", []) or d.get("data", [])
                    return [
                        {
                            "mac_address": c.get("mac", "").upper(),
                            "ip_address": c.get("ip", ""),
                            "host_name": c.get("name") or c.get("hostname") or "Unknown",
                            "status": "active" if c.get("active", 1) == 1 else "inactive",
                            "connection_type": c.get("type", "wireless"),
                        }
                        for c in clients
                    ]
                except (json.JSONDecodeError, ValueError):
                    pass

            r2 = self._api_get("dhcp?form=client")
            if r2.status_code == 200:
                try:
                    d = r2.json()
                    clients = d.get("data", {}).get("client_list", []) or d.get("data", [])
                    return [
                        {
                            "mac_address": c.get("mac", "").upper(),
                            "ip_address": c.get("ip", ""),
                            "host_name": c.get("name") or "Unknown",
                            "status": "active",
                        }
                        for c in clients
                    ]
                except (json.JSONDecodeError, ValueError):
                    pass

            return []
        except Exception:
            return []

    def get_bandwidth_usage(self) -> dict:
        try:
            r = self._api_get("network?form=statistics")
            if r.status_code == 200:
                try:
                    d = r.json().get("data", {})
                    rx = d.get("wan_rx_rate", 0) or d.get("wan_rx_bytes", 0)
                    tx = d.get("wan_tx_rate", 0) or d.get("wan_tx_bytes", 0)
                    
                    # FIXED: one-line ternary expressions
                    rx_mbps = round(rx / 1024 / 1024 * 8, 2) if rx < 1e9 else round(rx / 1e6, 2)
                    tx_mbps = round(tx / 1024 / 1024 * 8, 2) if tx < 1e9 else round(tx / 1e6, 2)
                    
                    return {
                        "download_mbps": rx_mbps,
                        "upload_mbps": tx_mbps,
                        "total_mbps": round(rx_mbps + tx_mbps, 2),
                    }
                except (json.JSONDecodeError, ValueError):
                    pass
            return {"total_mbps": 0.0, "download_mbps": 0.0, "upload_mbps": 0.0}
        except Exception:
            return {"total_mbps": 0.0, "download_mbps": 0.0, "upload_mbps": 0.0}

    def reboot(self) -> bool:
        try:
            r = self._api_post("system?form=reboot", data={"operation": "reboot"})
            if r.status_code == 200:
                return True
            r2 = self.session.post(
                f"{self.base_url}/userRpm/SysRebootRpm.htm?Reboot=Reboot",
                timeout=10,
                verify=False,
            )
            return r2.status_code == 200
        except Exception:
            return False

    def update_wifi_settings(self, ssid: str, password: str, **kwargs) -> bool:
        try:
            band = kwargs.get("band", "2.4")
            iface_id = 0 if band == "2.4" else 1

            payload = {
                "operation": "write",
                "iface": iface_id,
                "ssid": ssid,
                "password": password,
                "encryption": "WPA2-PSK",
                "hidden": kwargs.get("hidden", False),
            }

            r = self._api_post("wireless?form=status", data=payload)
            if r.status_code == 200:
                try:
                    d = r.json()
                    return d.get("success", True) or d.get("error_code", 0) == 0
                except (json.JSONDecodeError, ValueError):
                    return True

            guest_payload = {
                "operation": "write",
                "guest_2g": {
                    "ssid": ssid,
                    "password": password,
                    "enable": True,
                },
                "guest_5g": {
                    "ssid": f"{ssid}_5G",
                    "password": password,
                    "enable": True,
                },
            }
            r2 = self._api_post("wireless?form=guest", data=guest_payload)
            return r2.status_code == 200
        except Exception:
            return False

    def apply_bandwidth_limit(self, ip: str, limit_mbps: int) -> bool:
        try:
            payload = {
                "operation": "add",
                "ip": ip,
                "up_limit": limit_mbps * 1024,
                "down_limit": limit_mbps * 1024,
            }
            r = self._api_post("qos?form=rule", data=payload)
            if r.status_code == 200:
                return True
            return False
        except Exception:
            return False

    def block_mac(self, mac_address: str) -> bool:
        try:
            payload = {
                "operation": "add",
                "mac": mac_address.upper(),
                "type": "black",
            }
            r = self._api_post("access_control?form=blacklist", data=payload)
            if r.status_code == 200:
                return True

            self._api_post("access_control?form=enable", data={"enable": 1})
            r2 = self._api_post("access_control?form=list", data=payload)
            return r2.status_code == 200
        except Exception:
            return False

    def unblock_mac(self, mac_address: str) -> bool:
        try:
            payload = {
                "operation": "delete",
                "mac": mac_address.upper(),
                "type": "black",
            }
            r = self._api_post("access_control?form=blacklist", data=payload)
            if r.status_code == 200:
                return True

            r2 = self._api_post("access_control?form=list", data=payload)
            return r2.status_code == 200
        except Exception:
            return False