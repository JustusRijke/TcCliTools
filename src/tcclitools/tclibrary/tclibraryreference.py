"""A TwinCAT library reference"""
from __future__ import annotations

import re

from packaging import version as version_module

from .exceptions import TcLibraryException


class TcLibraryReference:
    """A TwinCAT library reference"""

    _RE_LIBRARY_REF = re.compile(r"^(.*), (.*) \((.*)\)")

    def __init__(self, title, version, company):
        self.title: str = title
        self.version: str | version_module.Version = version
        self.company: str = company

    def is_any_version(self):
        """Return True if version is any (e.g., "*")"""
        return isinstance(self.version, str) and self.version == "*"

    @staticmethod
    def parse_string(
        full_name,
    ) -> tuple[str, str | version_module.Version, str] | None:
        """Retrieve title, version and company from a string
        that matches the Beckhoff format
        (e.g, `"Tc2_Standard, 3.3.3.0 (Beckhoff Automation GmbH)"`)
        """
        try:
            res = TcLibraryReference._RE_LIBRARY_REF.match(full_name)
            title = res.group(1)  # type:ignore
            version = res.group(2)  # type:ignore
            company = res.group(3)  # type:ignore
            return (  # type:ignore
                title,
                version if version == "*" else version_module.parse(version),
                company,
            )
        except Exception as exc:
            raise TcLibraryException(f'Invalid library string: "{full_name}"') from exc

    @staticmethod
    def from_string(full_name):
        """Create a TcLibraryReference instance from a string
        that matches the Beckhoff format
        (e.g, `"Tc2_Standard, 3.3.3.0 (Beckhoff Automation GmbH)"`)
        """
        return TcLibraryReference(*TcLibraryReference.parse_string(full_name))

    @staticmethod
    def select_latest(
        references: list[TcLibraryReference],
    ) -> TcLibraryReference | None:
        """Return the library reference with the latest version
        out of a collection of library references."""
        if not references:
            return None
        if len(references) == 1:
            return references[0]
        # Assert that all libraries have the same title and company
        if any(
            [
                (
                    ref.title != references[0].title
                    or ref.company != references[0].company
                )
                for ref in references
            ]
        ):
            raise TcLibraryException(
                "Library references do not have matching title and company"
            )

        return sorted(references, key=lambda x: x.version)[-1]

    def __str__(self) -> str:
        """Custom __str__ implementation
        that matches the Beckhoff format
        (e.g, `"Tc2_Standard, 3.3.3.0 (Beckhoff Automation GmbH)"`)
        """
        return f"{self.title}, {self.version} ({self.company})"

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.title}", "{self.version}", "{self.company}")'

    def __eq__(self, other) -> bool:
        return isinstance(other, TcLibraryReference) and (
            (
                (self.version == other.version)
                or self.is_any_version()
                or other.is_any_version()
            )
            and self.title.lower() == other.title.lower()
            and self.company.lower() == other.company.lower()
        )

    def __gt__(self, other) -> bool:
        return (
            (self.is_any_version() or (self.version > other.version))
            and self.title.lower() == other.title.lower()
            and self.company.lower() == other.company.lower()
        )

    def __ge__(self, other) -> bool:
        return self.__gt__(other) or self.__eq__(other)

    def __hash__(self) -> int:
        return hash(str(self))
