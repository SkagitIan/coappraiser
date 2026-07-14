# Preflight ingestion

Uploads are classified by content signature and extension. ZIP members are checked for traversal, file-count, and expanded-size limits. Files are deduplicated by SHA-256. XML is stored as bounded text, PDF text is extracted with the existing pypdf helper, and images receive basic metadata. The current synchronous path is intentionally simple; long-running parsing should move to the existing worker infrastructure when required.
