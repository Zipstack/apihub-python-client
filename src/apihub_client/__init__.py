"""
ApiHub Python Client

A dynamic, extensible Python client for the APIHUB service supporting
any APIs following the extract → status → retrieve pattern.
"""

from .client import ApiHubClient, ApiHubClientException

__version__ = "0.0.0"
__author__ = "Unstract Team"
__email__ = "support@unstract.com"

__all__ = ["ApiHubClient", "ApiHubClientException"]
