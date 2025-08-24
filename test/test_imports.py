"""Test module imports and package-level functionality."""


class TestPackageImports:
    """Test cases for package imports."""

    def test_main_package_imports(self):
        """Test importing main classes from the package."""
        # This should import all main classes and trigger __init__.py coverage
        from apihub_client import (
            ApiHubClient,
            ApiHubClientException,
            DocSplitterClient,
            GenericUnstractClient,
        )

        # Verify classes are importable and are actually classes
        assert ApiHubClient is not None
        assert ApiHubClientException is not None
        assert DocSplitterClient is not None
        assert GenericUnstractClient is not None

        # Verify they are actually classes/exceptions
        assert callable(ApiHubClient)
        assert callable(ApiHubClientException)
        assert callable(DocSplitterClient)
        assert callable(GenericUnstractClient)

    def test_package_metadata(self):
        """Test package metadata is accessible."""
        import apihub_client

        # Check metadata attributes exist
        assert hasattr(apihub_client, "__version__")
        assert hasattr(apihub_client, "__author__")
        assert hasattr(apihub_client, "__email__")
        assert hasattr(apihub_client, "__all__")

        # Check metadata values
        assert apihub_client.__version__ == "0.1.1"
        assert apihub_client.__author__ == "Unstract Team"
        assert apihub_client.__email__ == "support@unstract.com"

        # Check __all__ contains expected items
        expected_all = [
            "ApiHubClient",
            "ApiHubClientException",
            "DocSplitterClient",
            "GenericUnstractClient",
        ]
        assert apihub_client.__all__ == expected_all

    def test_direct_module_imports(self):
        """Test direct module imports work."""
        from apihub_client.client import ApiHubClient, ApiHubClientException
        from apihub_client.doc_splitter import DocSplitterClient
        from apihub_client.generic_client import GenericUnstractClient

        # Verify classes are importable
        assert ApiHubClient is not None
        assert ApiHubClientException is not None
        assert DocSplitterClient is not None
        assert GenericUnstractClient is not None

    def test_client_instantiation(self):
        """Test that clients can be instantiated from package imports."""
        from apihub_client import (
            ApiHubClient,
            DocSplitterClient,
            GenericUnstractClient,
        )

        # Test ApiHubClient instantiation
        api_client = ApiHubClient(api_key="test_key", base_url="https://test.com")
        assert api_client.api_key == "test_key"
        assert api_client.base_url == "https://test.com"

        # Test DocSplitterClient instantiation
        doc_client = DocSplitterClient(api_key="test_key", base_url="https://test.com")
        assert doc_client.api_key == "test_key"
        assert doc_client.base_url == "https://test.com"

        # Test GenericUnstractClient instantiation
        generic_client = GenericUnstractClient(
            api_key="test_key", base_url="https://test.com"
        )
        assert generic_client.api_key == "test_key"
        assert generic_client.base_url == "https://test.com"

    def test_exception_instantiation(self):
        """Test that exception can be instantiated from package imports."""
        from apihub_client import ApiHubClientException

        # Test exception creation
        exc = ApiHubClientException("Test message", 400)
        assert exc.message == "Test message"
        assert exc.status_code == 400

        # Test exception string representation
        str_repr = str(exc)
        assert "Test message" in str_repr
        assert "400" in str_repr

    def test_star_import(self):
        """Test that star import works correctly."""
        # This imports everything in __all__
        exec("from apihub_client import *")  # noqa: S102

        # Check that the main classes are available in local scope
        locals_dict = locals()
        assert "ApiHubClient" in locals_dict
        assert "ApiHubClientException" in locals_dict
        assert "DocSplitterClient" in locals_dict
        assert "GenericUnstractClient" in locals_dict

    def test_package_docstring(self):
        """Test package docstring is accessible."""
        import apihub_client

        assert apihub_client.__doc__ is not None
        assert "Unstract API Hub Python Client" in apihub_client.__doc__
        assert "dynamic, extensible Python client" in apihub_client.__doc__

    def test_import_order_independence(self):
        """Test that imports work regardless of order."""
        # Import in different order
        from apihub_client import (
            ApiHubClient,  # noqa: F401
            ApiHubClientException,  # noqa: F401
            DocSplitterClient,  # noqa: F401
            GenericUnstractClient,
        )

        # Should work fine
        client = GenericUnstractClient(api_key="test", base_url="https://test.com")
        assert client.api_key == "test"

    def test_submodule_access(self):
        """Test that submodules are accessible through the package."""
        import apihub_client

        # Should be able to access submodules
        assert hasattr(apihub_client, "client")
        assert hasattr(apihub_client, "doc_splitter")
        assert hasattr(apihub_client, "generic_client")

        # Should be able to access classes through submodules
        assert hasattr(apihub_client.client, "ApiHubClient")
        assert hasattr(apihub_client.client, "ApiHubClientException")
        assert hasattr(apihub_client.doc_splitter, "DocSplitterClient")
        assert hasattr(apihub_client.generic_client, "GenericUnstractClient")
