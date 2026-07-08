#!/usr/bin/env python3
"""Public-output helpers for AINP CLI tools.

These helpers keep JSON/text output repo-relative and safe to paste into public
logs. They do not affect what validators read or verify.
"""
from __future__ import annotations

import os
import re
import urllib.parse


PATH_EXTENSIONS = r"(?:ainp|aisop|csv|docx?|gif|html?|jpe?g|json|md|pdf|png|py|txt|xlsx?)"
PATH_TEXT_BOUNDARY = r"(?=$|['\"<>)]|\r|\n)"
UNSAFE_FILE_URI_WITH_SPACES_RE = re.compile(
    rf"\b(file):[^'\"<>)]*?\.{PATH_EXTENSIONS}\b",
    re.IGNORECASE,
)
UNSAFE_FILE_URI_BROAD_RE = re.compile(
    r"\b(file):(?=//|[A-Za-z]:|[\\/])[^'\"<>\r\n)]*",
    re.IGNORECASE,
)
UNSAFE_FILE_URI_RE = re.compile(r"\b(file):[^\s'\"<>)]{1,}", re.IGNORECASE)
UNSAFE_URI_RE = re.compile(r"\b(javascript|data|vbscript):[^\s'\"<>)]{1,}", re.IGNORECASE)
ENCODED_UNSAFE_URI_RE = re.compile(
    r"(?<![A-Za-z0-9+.-])(?=[^\s'\"<>)]*%)[^\s'\"<>)]{3,}",
    re.IGNORECASE,
)
WINDOWS_USER_PATH_BROAD_RE = re.compile(
    r"(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/]*Users[\\/][^'\"<>\r\n)]*?" + PATH_TEXT_BOUNDARY,
    re.IGNORECASE,
)
WINDOWS_USER_PATH_WITH_SPACES_RE = re.compile(
    rf"(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/]*Users[\\/][^'\"<>)]*?\.{PATH_EXTENSIONS}\b",
    re.IGNORECASE,
)
WINDOWS_USER_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/]*Users[\\/][^\s'\"<>)]*",
    re.IGNORECASE,
)
WINDOWS_LOCAL_PATH_WITH_SPACES_RE = re.compile(
    rf"(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/][^'\"<>)]*?\.{PATH_EXTENSIONS}\b",
    re.IGNORECASE,
)
WINDOWS_LOCAL_PATH_BROAD_RE = re.compile(
    r"(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/][^'\"<>\r\n)]*?" + PATH_TEXT_BOUNDARY,
    re.IGNORECASE,
)
WINDOWS_LOCAL_PATH_RE = re.compile(
    rf"(?<![A-Za-z0-9+.-])[A-Za-z]:(?:[\\/][^\s'\"<>)]*|"
    rf"[^\s'\"<>)]*?\.{PATH_EXTENSIONS}\b[^\s'\"<>)]*)",
    re.IGNORECASE,
)
WINDOWS_DRIVE_RELATIVE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9+.-])[A-Za-z]:(?![\\/\s])[^\s'\"<>)]*",
    re.IGNORECASE,
)
UNC_PATH_WITH_SPACES_RE = re.compile(
    rf"(?<![A-Za-z0-9+.-:])(?:\\\\|//)[^\\/\s'\"<>]+[\\/][^'\"<>)]*?\.{PATH_EXTENSIONS}\b",
    re.IGNORECASE,
)
UNC_PATH_BROAD_RE = re.compile(
    r"(?<![A-Za-z0-9+.-:])(?:\\\\|//)[^\\/\s'\"<>]+[\\/][^'\"<>\r\n)]*?" + PATH_TEXT_BOUNDARY
)
UNC_PATH_RE = re.compile(r"(?<![A-Za-z0-9+.-:])(?:\\\\|//)[^\\/\s'\"<>]+[\\/][^\s'\"<>)]*")
POSIX_LOCAL_PATH_BROAD_RE = re.compile(
    r"(?<![A-Za-z0-9+.-:])/"
    r"(?:Users|home|tmp|var|private|mnt|workspace|workspaces|root|run|opt/hostedtoolcache)"
    r"[^'\"<>\r\n)]*?"
    + PATH_TEXT_BOUNDARY,
    re.IGNORECASE,
)
DRIVE_RELATIVE_RE = re.compile(r"^[A-Za-z]:(?![\\/])")


class PublicOutput:
    def __init__(self, tool_file: str | None = None,
                 bases: list[str | None] | None = None) -> None:
        self.bases: list[str] = []
        self.add_base(os.getcwd())
        if tool_file:
            self.add_base(os.path.dirname(os.path.dirname(os.path.abspath(tool_file))))
        for base in bases or []:
            self.add_base(base)

    @staticmethod
    def _inside(base: str, path: str) -> bool:
        try:
            base_real = os.path.normcase(os.path.realpath(base))
            path_real = os.path.normcase(os.path.realpath(path))
            return os.path.commonpath([base_real, path_real]) == base_real
        except ValueError:
            return False

    @staticmethod
    def _path_variants(path: str) -> set[str]:
        path = os.path.abspath(path)
        return {
            path,
            path.replace(os.sep, "/"),
            path.replace("\\", "\\\\"),
        }

    def add_base(self, path: str | None) -> None:
        if not path:
            return
        base = os.path.abspath(path)
        if base not in self.bases:
            self.bases.append(base)

    def register_input_path(self, path: str | None) -> None:
        if path:
            self.add_base(os.path.dirname(os.path.abspath(path)))

    def display_path(self, path: str) -> str:
        if not path:
            return path
        if UNC_PATH_RE.search(path):
            return self.sanitize_text(path)
        if DRIVE_RELATIVE_RE.match(path):
            sanitized = self.sanitize_text(path)
            return sanitized if sanitized != path else "<local-machine-path>"
        if os.path.isabs(path):
            for base in self.bases:
                if self._inside(base, path):
                    return os.path.relpath(path, base).replace(os.sep, "/").replace("\\", "/")
            return os.path.basename(path)
        sanitized = self.sanitize_text(path)
        if sanitized != path:
            return sanitized
        return path.replace(os.sep, "/").replace("\\", "/")

    def sanitize_text(self, text: str) -> str:
        out = text
        flags = re.IGNORECASE if os.name == "nt" else 0
        for base in self.bases:
            for variant in self._path_variants(base):
                out = re.sub(re.escape(variant), ".", out, flags=flags)
        out = ENCODED_UNSAFE_URI_RE.sub(self._redact_encoded_unsafe_uri, out)
        out = UNSAFE_FILE_URI_WITH_SPACES_RE.sub(lambda m: f"{m.group(1).lower()}:<redacted>", out)
        out = UNSAFE_FILE_URI_BROAD_RE.sub(lambda m: f"{m.group(1).lower()}:<redacted>", out)
        out = UNSAFE_FILE_URI_RE.sub(lambda m: f"{m.group(1).lower()}:<redacted>", out)
        out = UNSAFE_URI_RE.sub(lambda m: f"{m.group(1).lower()}:<redacted>", out)
        out = WINDOWS_USER_PATH_BROAD_RE.sub("<local-machine-path>", out)
        out = WINDOWS_USER_PATH_WITH_SPACES_RE.sub("<local-machine-path>", out)
        out = WINDOWS_USER_PATH_RE.sub("<local-machine-path>", out)
        out = UNC_PATH_BROAD_RE.sub("<local-machine-path>", out)
        out = UNC_PATH_WITH_SPACES_RE.sub("<local-machine-path>", out)
        out = UNC_PATH_RE.sub("<local-machine-path>", out)
        out = POSIX_LOCAL_PATH_BROAD_RE.sub("<local-machine-path>", out)
        out = WINDOWS_DRIVE_RELATIVE_PATH_RE.sub("<local-machine-path>", out)
        out = WINDOWS_LOCAL_PATH_BROAD_RE.sub("<local-machine-path>", out)
        out = WINDOWS_LOCAL_PATH_WITH_SPACES_RE.sub("<local-machine-path>", out)
        out = WINDOWS_LOCAL_PATH_RE.sub("<local-machine-path>", out)
        return out.replace("\\", "/")

    @staticmethod
    def _redact_encoded_unsafe_uri(match: re.Match) -> str:
        token = match.group(0)
        decoded = token
        for _ in range(3):
            next_decoded = urllib.parse.unquote(decoded)
            if next_decoded == decoded:
                break
            decoded = next_decoded
        lower = decoded.lower()
        for scheme in ("file", "javascript", "data", "vbscript"):
            if lower.startswith(f"{scheme}:"):
                return f"{scheme}:<redacted>"
        return token

    def public_findings(self, findings: list[dict]) -> list[dict]:
        public = []
        for item in findings:
            copy = dict(item)
            if isinstance(copy.get("path"), str):
                copy["path"] = self.display_path(copy["path"])
            if isinstance(copy.get("message"), str):
                copy["message"] = self.sanitize_text(copy["message"])
            public.append(copy)
        return public
