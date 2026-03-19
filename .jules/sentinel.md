## 2025-05-22 - [Path Traversal in Document Uploads]
**Vulnerability:** User-provided filenames in the Knowledge Vault upload feature were not sanitized, allowing attackers to write files outside the intended `documents/` directory using path traversal sequences like `../`.
**Learning:** Even in local-first applications, file upload features must treat filenames as untrusted input. Using `os.path.basename()` is a simple but effective defense to strip directory information.
**Prevention:** Always sanitize filenames from external inputs before using them in file system operations. Consider using `os.path.basename()` or a secure filename utility.
