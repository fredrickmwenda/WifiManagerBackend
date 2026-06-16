from .base import RouterConnector
from .tplink import TPLinkConnector
from .mikrotik import MikroTikConnector
from .cisco import CiscoConnector
from .huawei import HuaweiConnector
from .generic import GenericConnector

CONNECTOR_MAP = {
    'tp-link': TPLinkConnector,
    'mikrotik': MikroTikConnector,
    'cisco': CiscoConnector,
    'huawei': HuaweiConnector,
    'ubiquiti': GenericConnector,
    'generic': GenericConnector,
}

def get_connector(router):
    """
    Factory: returns the correct connector instance for a router record.
    """
    connector_class = CONNECTOR_MAP.get(router.router_type, GenericConnector)
    return connector_class(router)