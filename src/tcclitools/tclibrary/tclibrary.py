"""A TwinCAT library"""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from packaging import version as version_module

from tcclitools.uniquepath import UniquePath

from . import TcLibraryException
from .tclibraryreference import TcLibraryReference


class TcLibrary(TcLibraryReference, UniquePath):
    """A TwinCAT library"""

    # https://stackoverflow.com/questions/53518981/inheritance-hash-sets-to-none-in-a-subclass
    __hash__ = UniquePath.__hash__  # type:ignore

    def __init__(
        self,
        path: Path,
    ) -> None:
        """Initialize a TcLibrary from a PLC project file (`.plcproj`) or a folder
        in the Library Repository.

        The default Library Repository folder is
        `C:\\TwinCAT\\3.1\\Components\\Plc\\Managed Libraries`
        The specified folder must contain a `browsercache.` file which contains the
        library properties (name, version and company)."""

        self._allowed_types = [".plcproj", None]
        UniquePath.__init__(self, path)

        if path.is_dir():  # Must be a library repository folder
            self.path = path
            path_browsercache = path / "browsercache"
            if not path_browsercache.exists():
                raise FileNotFoundError(
                    f"Missing browsercache file in directory '{path}'"
                )
            try:
                full_name = (
                    ElementTree.parse(path_browsercache).getroot().attrib["Name"]
                )
                (title, version, company) = self.parse_string(  # type:ignore
                    full_name
                )
            except Exception as exc:
                raise TcLibraryException(
                    f'Invalid browsercache file: "{path_browsercache}"'
                ) from exc

        else:  # Must be a .plcproj file
            try:
                xmlroot = ElementTree.parse(path).getroot()
                (title, version, company) = [  # type:ignore
                    xmlroot.find(
                        "./{*}PropertyGroup/{*}" + find_str
                    ).text  # type:ignore
                    for find_str in ["Title", "ProjectVersion", "Company"]
                ]
                version = version_module.parse(version)  # type:ignore
            except Exception as exc:
                raise TcLibraryException(f'Not a valid library: "{path}"') from exc

        TcLibraryReference.__init__(
            self,
            title=title,
            version=version,  # type:ignore
            company=company,
        )

    def as_reference(self):
        """Return a TcLibraryReference instance"""
        return TcLibraryReference(self.title, self.version, self.company)

    @staticmethod
    def get_library_repository(
        tc_path: Path = Path("C:\\TwinCAT\\3.1\\Components\\Plc\\Managed Libraries"),
    ) -> list[TcLibrary]:
        """Return libraries from a library repository.
        Defaults to the `C:\\TwinCAT\\3.1\\Components\\Plc\\Managed Libraries` folder."""

        if not tc_path.exists():
            raise FileNotFoundError(f"Path '{tc_path}' does not exist!")

        libs = []
        for path in tc_path.glob("**/browsercache"):
            libs.append(TcLibrary(path.parent))

        return libs
