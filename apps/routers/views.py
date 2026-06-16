from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Router, RouterMacFilter, RouterSyncLog
from .serializers import (
    RouterSerializer,
    RouterListSerializer,
    RouterMacFilterSerializer,
    RouterSyncLogSerializer,
)
from .services import RouterService


class RouterMacFilterViewSet(viewsets.ModelViewSet):
    queryset = RouterMacFilter.objects.all()
    serializer_class = RouterMacFilterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["router", "is_active", "bypass_subscription"]
    search_fields = ["mac_address", "name"]


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "router_type", "access_mode", "connection_status"]
    search_fields = ["name", "ip_address", "location_tag"]

    def get_serializer_class(self):
        if self.action == "list":
            return RouterListSerializer
        return RouterSerializer

    @action(detail=True, methods=["post"])
    def test_connection(self, request, pk=None):
        router = self.get_object()
        service = RouterService(router)
        ok = service.test_connection()
        return Response(
            {
                "connected": ok,
                "connection_status": router.connection_status,
                "error": router.connection_error,
            },
            status=status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        router = self.get_object()
        service = RouterService(router)
        ok = service.sync()
        serializer = self.get_serializer(router)
        data = serializer.data
        data["sync_success"] = ok
        return Response(
            data,
            status=status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @action(detail=True, methods=["post"])
    def discover_devices(self, request, pk=None):
        router = self.get_object()
        service = RouterService(router)
        discovered = service.discover_devices()
        return Response(
            {"discovered_count": len(discovered), "devices": discovered}
        )

    @action(detail=True, methods=["post"])
    def restart(self, request, pk=None):
        router = self.get_object()
        service = RouterService(router)
        ok = service.reboot()
        if ok:
            router.status = "rebooting"
            router.save(update_fields=["status"])
        return Response(
            {
                "detail": "Reboot command issued." if ok else "Reboot failed.",
                "success": ok,
            },
            status=status.HTTP_202_ACCEPTED if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @action(detail=True, methods=["post"])
    def set_active(self, request, pk=None):
        Router.objects.update(is_active_setup=False)
        router = self.get_object()
        router.is_active_setup = True
        router.save()
        return Response({"detail": f"{router.name} is now the active router."})

    @action(detail=True, methods=["post"], url_path="bulk-mac-filters")
    def bulk_mac_filters(self, request, pk=None):
        router = self.get_object()
        macs = request.data.get("macs", [])
        if not isinstance(macs, list):
            return Response(
                {"detail": "macs must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_ids = []
        for item in macs:
            mac = item.get("mac_address", "").strip()
            if not mac:
                continue
            obj, _ = RouterMacFilter.objects.get_or_create(
                router=router,
                mac_address__iexact=mac,
                defaults={
                    "mac_address": mac,
                    "name": item.get("name", ""),
                    "bypass_subscription": item.get("bypass_subscription", True),
                    "is_active": item.get("is_active", True),
                },
            )
            created_ids.append(obj.id)

        return Response(
            {
                "router": router.id,
                "created_or_updated": len(created_ids),
                "ids": created_ids,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="apply-wifi")
    def apply_wifi(self, request, pk=None):
        router = self.get_object()
        ssid = request.data.get("ssid", router.ssid)
        password = request.data.get("password", router.wlan_key)
        service = RouterService(router)
        ok = service.apply_wifi(ssid, password)
        if ok:
            router.ssid = ssid
            router.wlan_key = password
            router.save(update_fields=["ssid", "wlan_key"])
        return Response(
            {
                "success": ok,
                "detail": "WiFi settings applied."
                if ok
                else "Failed to apply WiFi settings.",
            },
            status=status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @action(detail=True, methods=["post"], url_path="block-mac")
    def block_mac_router(self, request, pk=None):
        router = self.get_object()
        mac = request.data.get("mac_address")
        if not mac:
            return Response(
                {"detail": "mac_address required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        service = RouterService(router)
        ok = service.block_mac(mac)
        return Response(
            {"success": ok, "detail": "MAC blocked." if ok else "Failed."}
        )

    @action(detail=True, methods=["post"], url_path="unblock-mac")
    def unblock_mac_router(self, request, pk=None):
        router = self.get_object()
        mac = request.data.get("mac_address")
        if not mac:
            return Response(
                {"detail": "mac_address required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        service = RouterService(router)
        ok = service.unblock_mac(mac)
        return Response(
            {"success": ok, "detail": "MAC unblocked." if ok else "Failed."}
        )

    @action(detail=True, methods=["get"], url_path="sync-logs")
    def sync_logs(self, request, pk=None):
        router = self.get_object()
        logs = router.sync_logs.order_by("-created_at")[:50]
        serializer = RouterSyncLogSerializer(logs, many=True)
        return Response(serializer.data)