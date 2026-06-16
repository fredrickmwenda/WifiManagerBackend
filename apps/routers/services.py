from django.utils import timezone
from utils.router_connectors import get_connector
from .models import RouterSyncLog


class RouterService:
    def __init__(self, router):
        self.router = router
        self.connector = get_connector(router)

    def test_connection(self):
        ok = self.connector.connect()
        if ok:
            self.router.connection_status = "connected"
            self.router.connection_error = ""
        else:
            self.router.connection_status = "failed"
        self.router.save(update_fields=["connection_status", "connection_error"])
        self.connector.disconnect()
        return ok

    def sync(self):
        self.router.connection_status = "syncing"
        self.router.save(update_fields=["connection_status"])
        try:
            if not self.connector.connect():
                raise Exception(
                    "Connection failed: " + (self.router.connection_error or "unknown")
                )

            info = self.connector.get_system_info()
            if info.get("name"):
                self.router.name = info["name"]
            if info.get("firmware"):
                self.router.firmware = info["firmware"]
            if info.get("uptime"):
                self.router.uptime = info["uptime"]
            if info.get("model"):
                self.router.model_name = info["model"]

            bw = self.connector.get_bandwidth_usage()
            self.router.current_bandwidth_usage = bw.get("total_mbps", 0)

            self.router.last_synced_at = timezone.now()
            self.router.connection_status = "connected"
            self.router.connection_error = ""
            self.router.save()

            RouterSyncLog.objects.create(
                router=self.router,
                action="sync",
                status="success",
                details={"info": info, "bandwidth": bw},
            )
            return True
        except Exception as e:
            self.router.connection_status = "failed"
            self.router.connection_error = str(e)
            self.router.save()
            RouterSyncLog.objects.create(
                router=self.router, action="sync", status="failed", message=str(e)
            )
            return False
        finally:
            self.connector.disconnect()

    def discover_devices(self):
        if not self.connector.connect():
            return []
        try:
            leases = self.connector.get_dhcp_leases()
            from apps.devices.models import Device

            results = []
            for lease in leases:
                if not lease.get("mac_address"):
                    continue
                device, is_new = Device.objects.update_or_create(
                    mac_address=lease["mac_address"].upper(),
                    defaults={
                        "ip_address": lease.get("ip_address", "0.0.0.0"),
                        "name": lease.get("host_name") or "Unknown",
                        "router": self.router,
                        "status": "connected"
                        if lease.get("status") == "active"
                        else "disconnected",
                        "device_type": self._guess_device_type(
                            lease.get("host_name", "")
                        ),
                    },
                )
                results.append(
                    {
                        "mac_address": lease["mac_address"],
                        "ip_address": lease.get("ip_address"),
                        "name": device.name,
                        "created": is_new,
                        "status": device.status,
                    }
                )
            RouterSyncLog.objects.create(
                router=self.router,
                action="discover",
                status="success",
                details={"count": len(results)},
            )
            return results
        except Exception as e:
            RouterSyncLog.objects.create(
                router=self.router, action="discover", status="failed", message=str(e)
            )
            return []
        finally:
            self.connector.disconnect()

    def _guess_device_type(self, hostname):
        h = (hostname or "").lower()
        if any(x in h for x in ["iphone", "samsung", "pixel", "xiaomi", "android"]):
            return "phone"
        if any(x in h for x in ["macbook", "laptop", "thinkpad", "dell"]):
            return "laptop"
        if any(x in h for x in ["tv", "samsung_tv", "roku", "firetv"]):
            return "tv"
        if any(x in h for x in ["ipad", "tablet"]):
            return "tablet"
        if any(x in h for x in ["game", "xbox", "playstation", "ps5", "nintendo"]):
            return "gaming"
        return "other"

    def reboot(self):
        try:
            if not self.connector.connect():
                return False
            ok = self.connector.reboot()
            RouterSyncLog.objects.create(
                router=self.router,
                action="reboot",
                status="success" if ok else "failed",
            )
            return ok
        except Exception as e:
            RouterSyncLog.objects.create(
                router=self.router, action="reboot", status="failed", message=str(e)
            )
            return False
        finally:
            self.connector.disconnect()

    def apply_wifi(self, ssid, password):
        try:
            if not self.connector.connect():
                return False
            ok = self.connector.update_wifi_settings(ssid, password)
            RouterSyncLog.objects.create(
                router=self.router,
                action="apply_wifi",
                status="success" if ok else "failed",
                details={"ssid": ssid},
            )
            return ok
        except Exception as e:
            RouterSyncLog.objects.create(
                router=self.router,
                action="apply_wifi",
                status="failed",
                message=str(e),
            )
            return False
        finally:
            self.connector.disconnect()

    def block_mac(self, mac_address):
        try:
            if not self.connector.connect():
                return False
            ok = self.connector.block_mac(mac_address)
            RouterSyncLog.objects.create(
                router=self.router,
                action="block_mac",
                status="success" if ok else "failed",
                details={"mac": mac_address},
            )
            return ok
        except Exception as e:
            RouterSyncLog.objects.create(
                router=self.router,
                action="block_mac",
                status="failed",
                message=str(e),
            )
            return False
        finally:
            self.connector.disconnect()

    def unblock_mac(self, mac_address):
        try:
            if not self.connector.connect():
                return False
            ok = self.connector.unblock_mac(mac_address)
            RouterSyncLog.objects.create(
                router=self.router,
                action="unblock_mac",
                status="success" if ok else "failed",
                details={"mac": mac_address},
            )
            return ok
        except Exception as e:
            RouterSyncLog.objects.create(
                router=self.router,
                action="unblock_mac",
                status="failed",
                message=str(e),
            )
            return False
        finally:
            self.connector.disconnect()