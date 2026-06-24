from utils.base import RouterConnector


try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
except ImportError:
    ConnectHandler = None
    NetmikoTimeoutException = Exception
    NetmikoAuthenticationException = Exception


class CiscoConnector(RouterConnector):
    """
    Cisco IOS / IOS-XE via SSH (Netmiko).
    For wireless controllers use a custom connector subclass.
    """

    def connect(self) -> bool:
        if ConnectHandler is None:
            self.router.connection_error = "netmiko not installed"
            return False
        try:
            device = {
                "device_type": "cisco_ios",
                "ip": str(self.router.ip_address),
                "username": self.router.username,
                "password": self.router.password,
                "port": self.router.port or 22,
                "timeout": 30,
            }
            self.connection = ConnectHandler(**device)
            return True
        except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
            self.router.connection_error = str(e)
            return False
        except Exception as e:
            self.router.connection_error = str(e)
            return False

    def disconnect(self):
        if self.connection:
            self.connection.disconnect()
            self.connection = None

    def get_system_info(self):
        try:
            output = self.connection.send_command("show version", use_textfsm=True)
            if isinstance(output, list) and len(output) > 0:
                d = output[0]
                return {
                    "name": d.get("hostname", self.router.name),
                    "firmware": d.get("version", ""),
                    "uptime": d.get("uptime", ""),
                    "model": d.get("hardware", ""),
                }
            return {}
        except Exception:
            return {}

    def get_dhcp_leases(self):
        try:
            output = self.connection.send_command(
                "show ip dhcp binding", use_textfsm=True
            )
            if isinstance(output, list):
                return [
                    {
                        "mac_address": o.get("mac_address", ""),
                        "ip_address": o.get("ip_address", ""),
                        "host_name": o.get("client_id") or "Unknown",
                        "status": "active",
                    }
                    for o in output
                ]
            return []
        except Exception:
            return []

    def get_bandwidth_usage(self):
        return {"total_mbps": 0.0, "download_mbps": 0.0, "upload_mbps": 0.0}

    def reboot(self):
        try:
            self.connection.send_command_timing("reload", strip_prompt=False)
            self.connection.send_command_timing("yes", strip_prompt=False)
            return True
        except Exception:
            return False

    def update_wifi_settings(self, ssid: str, password: str, **kwargs):
        return False

    def apply_bandwidth_limit(self, ip: str, limit_mbps: int):
        return False

    def block_mac(self, mac_address: str):
        try:
            cmd = f"mac address-table static {mac_address} vlan 1 drop"
            self.connection.send_command_timing(cmd)
            return True
        except Exception:
            return False

    def unblock_mac(self, mac_address: str):
        try:
            cmd = f"no mac address-table static {mac_address} vlan 1 drop"
            self.connection.send_command_timing(cmd)
            return True
        except Exception:
            return False