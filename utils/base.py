from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class RouterConnector(ABC):
    """
    Abstract base class that every vendor connector must implement.
    """

    def __init__(self, router):
        self.router = router
        self.connection = None

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection. Return True on success."""
        pass

    @abstractmethod
    def disconnect(self):
        """Tear down connection."""
        pass

    @abstractmethod
    def get_system_info(self) -> Dict[str, Any]:
        """Return dict with keys: name, firmware, uptime, model, cpu_load."""
        pass

    @abstractmethod
    def get_dhcp_leases(self) -> List[Dict[str, Any]]:
        """
        Return list of dicts:
        [{'mac_address': '...', 'ip_address': '...', 'host_name': '...', 'status': 'active'}, ...]
        """
        pass

    @abstractmethod
    def get_bandwidth_usage(self) -> Dict[str, float]:
        """Return {'total_mbps': 0.0, 'download_mbps': 0.0, 'upload_mbps': 0.0}."""
        pass

    @abstractmethod
    def reboot(self) -> bool:
        """Send hardware reboot command."""
        pass

    @abstractmethod
    def update_wifi_settings(self, ssid: str, password: str, **kwargs) -> bool:
        """Push SSID / WPA key to the radio."""
        pass

    @abstractmethod
    def apply_bandwidth_limit(self, ip: str, limit_mbps: int) -> bool:
        """Apply per-IP simple queue / policy."""
        pass

    @abstractmethod
    def block_mac(self, mac_address: str) -> bool:
        """Add MAC to hardware deny / ACL list."""
        pass

    @abstractmethod
    def unblock_mac(self, mac_address: str) -> bool:
        """Remove MAC from hardware deny / ACL list."""
        pass