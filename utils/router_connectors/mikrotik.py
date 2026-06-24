from utils.base import RouterConnector

try:
    from librouteros import connect
    from librouteros.exceptions import TrapError
except ImportError:
    connect = None
    TrapError = Exception


class MikroTikConnector(RouterConnector):
    """
    MikroTik RouterOS via librouteros (API port 8728/8729).
    """

    def connect(self) -> bool:
        if connect is None:
            self.router.connection_error = "librouteros not installed"
            return False
        try:
            self.connection = connect(
                username=self.router.username,
                password=self.router.password,
                host=str(self.router.ip_address),
                port=self.router.port or 8728,
            )
            return True
        except Exception as e:
            self.router.connection_error = str(e)
            return False

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

    def get_system_info(self):
        try:
            identity = list(self.connection.path("system", "identity").select())
            resource = list(self.connection.path("system", "resource").select())
            info = {
                "name": identity[0].get("name", "") if identity else "",
                "firmware": resource[0].get("version", "") if resource else "",
                "uptime": resource[0].get("uptime", "") if resource else "",
                "cpu_load": resource[0].get("cpu-load", 0) if resource else 0,
            }
            return info
        except Exception:
            return {}

    def get_dhcp_leases(self):
        try:
            leases = list(self.connection.path("ip", "dhcp-server", "lease").select())
            return [
                {
                    "mac_address": l.get("mac-address", ""),
                    "ip_address": l.get("address", ""),
                    "host_name": l.get("host-name") or l.get("comment") or "Unknown",
                    "status": "active" if l.get("status") == "bound" else "inactive",
                }
                for l in leases
            ]
        except Exception:
            return []

    def get_bandwidth_usage(self):
        try:
            # Read interface traffic monitor (simplified)
            # In production, call /interface/monitor-traffic via .call()
            return {"total_mbps": 0.0, "download_mbps": 0.0, "upload_mbps": 0.0}
        except Exception:
            return {"total_mbps": 0.0, "download_mbps": 0.0, "upload_mbps": 0.0}

    def reboot(self):
        try:
            self.connection.path("system", "reboot").call()
            return True
        except Exception:
            return False

    def update_wifi_settings(self, ssid: str, password: str, **kwargs):
        try:
            # Update security profile and wireless interface
            # This is config-dependent; below is a common pattern
            return False
        except Exception:
            return False

    def apply_bandwidth_limit(self, ip: str, limit_mbps: int):
        try:
            # Add simple queue
            self.connection.path("queue", "simple").add(
                name=f"limit-{ip}",
                target=ip,
                max_limit=f"{limit_mbps}M/{limit_mbps}M",
            )
            return True
        except Exception:
            return False

    def block_mac(self, mac_address: str):
        try:
            self.connection.path("interface", "wireless", "access-list").add(
                mac_address=mac_address,
                authentication="no",
                forwarding="no",
                comment="Blocked by WiFi Manager",
            )
            return True
        except Exception:
            return False

    def unblock_mac(self, mac_address: str):
        try:
            items = list(
                self.connection.path("interface", "wireless", "access-list").select()
            )
            for item in items:
                if item.get("mac-address", "").lower() == mac_address.lower():
                    self.connection.path("interface", "wireless", "access-list").remove(
                        item.get(".id")
                    )
            return True
        except Exception:
            return False