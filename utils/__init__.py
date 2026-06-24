from .base import RouterConnector
# get from router_connectors
from  .router_connectors.tplink import TPLinkConnector
from .router_connectors.mikrotik import MikroTikConnector
from .router_connectors.cisco import CiscoConnector
from .router_connectors.huawei import HuaweiConnector
from .router_connectors.generic import GenericConnector

CONNECTOR_MAP = {
    'tp-link': TPLinkConnector,
    'mikrotik': MikroTikConnector,
    'cisco': CiscoConnector,
    'huawei': HuaweiConnector,
    'ubiquiti': GenericConnector,
    'generic': GenericConnector,
}

def get_connector(router):
    connector_class = CONNECTOR_MAP.get(router.router_type, GenericConnector)
    return connector_class(router)