"""
Unstract API Hub Python Client

A dynamic, extensible Python client for the APIHUB service supporting
any APIs following the extract → status → retrieve pattern.
"""

from .client import ApiHubClient, ApiHubClientException
from .doc_splitter import DocSplitterClient
from .generic_client import GenericUnstractClient

__version__ = "0.2.1"
__author__ = "Unstract Team"
__email__ = "support@unstract.com"

__all__ = [
    "ApiHubClient",
    "ApiHubClientException",
    "DocSplitterClient",
    "GenericUnstractClient",
]
