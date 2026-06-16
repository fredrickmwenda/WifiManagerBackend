from .base import RouterConnector

try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
except ImportError:
    ConnectHandler = None
    NetmikoTimeoutException = Exception
    NetmikoAuthenticationException = Exception


class GenericConnector(RouterConnector):
    """
    Fallback for any SSH-capable device (Ubiquiti, Linux gateways, custom firmware).
    Uses Netmiko generic_termserver or paramiko under the hood.
    """

    def connect(self) -> bool:
        if ConnectHandler is None:
            self.router.connection_error = "netmiko not installed"
            return False
        try:
            device = {
                "device_type": "generic_termserver",
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
            output = self.connection.send_command("uname -a", expect_string=r"#")
            return {
                "name": self.router.name,
                "firmware": output[:100],
                "uptime": "",
            }
        except Exception:
            return {}

    def get_dhcp_leases(self):
        try:
            # Try dnsmasq leases file or DHCP server command
            output = self.connection.send_command(
                "cat /var/lib/misc/dnsmasq.leases", expect_string=r"#"
            )
            leases = []
            for line in output.strip().splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    leases.append(
                        {
                            "mac_address": parts[1],
                            "ip_address": parts[2],
                            "host_name": parts[3] if parts[3] != "*" else "Unknown",
                            "status": "active",
                        }
                    )
            return leases
        except Exception:
            return []

    def get_bandwidth_usage(self):
        return {"total_mbps": 0.0, "download_mbps": 0.0, "upload_mbps": 0.0}

    def reboot(self):
        try:
            self.connection.send_command_timing("reboot")
            return True
        except Exception:
            return False

    def update_wifi_settings(self, ssid: str, password: str, **kwargs):
        return False

    def apply_bandwidth_limit(self, ip: str, limit_mbps: int):
        return False

    def block_mac(self, mac_address: str):
        return False

    def unblock_mac(self, mac_address: str):
        return False