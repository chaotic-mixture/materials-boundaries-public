"""Bounded native-Windows composite saving on local NTFS volumes.

Only this private backend uses Win32, via the standard library's ctypes. Each
ancestor directory is opened without following its final reparse point and
held without delete sharing. This is not a hostile-writer or crash guarantee.
See docs/COMPOSITE_WORKFLOW.md for supported paths and the API references.
"""
from __future__ import annotations

from contextlib import contextmanager, ExitStack
import ctypes
from ctypes import wintypes
import os
from pathlib import Path, PureWindowsPath
import secrets
import stat

from .validation import ValidationError

_FILE_ATTRIBUTE_DIRECTORY = 0x10
_FILE_ATTRIBUTE_REPARSE_POINT = 0x400
_DIRECTORY_READ_ACCESS = 0x1 | 0x80  # FILE_LIST_DIRECTORY | FILE_READ_ATTRIBUTES
_FILE_SHARE_READ_WRITE = 0x3  # Deliberately omit FILE_SHARE_DELETE.
_OPEN_EXISTING = 3
_DIRECTORY_FLAGS = 0x02000000 | 0x00200000  # BACKUP_SEMANTICS | OPEN_REPARSE_POINT
_INVALID_HANDLE = ctypes.c_void_p(-1).value
_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'} | {
    prefix + suffix for prefix in ('COM', 'LPT') for suffix in '123456789¹²³'
}


class _FileInformation(ctypes.Structure):
    _fields_ = [
        ('attributes', wintypes.DWORD), ('created', wintypes.FILETIME),
        ('accessed', wintypes.FILETIME), ('written', wintypes.FILETIME),
        ('volume', wintypes.DWORD), ('size_high', wintypes.DWORD),
        ('size_low', wintypes.DWORD), ('links', wintypes.DWORD),
        ('index_high', wintypes.DWORD), ('index_low', wintypes.DWORD),
    ]


def _api():
    if os.name != 'nt':
        raise ValidationError('output: native Windows export is unavailable on this platform')
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                               wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    api.CreateFileW.restype = wintypes.HANDLE
    api.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(_FileInformation)]
    api.GetFileInformationByHandle.restype = wintypes.BOOL
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    api.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
    api.GetDriveTypeW.restype = wintypes.UINT
    api.GetVolumeInformationByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR,
        wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR, wintypes.DWORD]
    api.GetVolumeInformationByHandleW.restype = wintypes.BOOL
    return api


def _error(path):
    error = ctypes.WinError(ctypes.get_last_error())
    error.filename = str(path)
    return error


def _checked_spelling(raw: str) -> PureWindowsPath:
    """Check before normalization; never sanitize ambiguous Windows names."""
    if not isinstance(raw, str) or not raw or '\x00' in raw:
        raise ValidationError('output: expected a nonempty local path without NUL')
    spelling = raw.replace('/', '\\')
    path = PureWindowsPath(spelling)
    if spelling.startswith('\\\\') or (path.drive and (len(path.drive) != 2 or path.drive[1] != ':')):
        raise ValidationError('output: UNC and device-namespace paths are not supported')
    if path.root and not path.drive:
        raise ValidationError('output: root-relative paths are not supported')
    if path.drive and (not path.drive[0].isascii() or not path.drive[0].isalpha()):
        raise ValidationError('output: expected a local drive letter')
    if path.drive and not path.root:
        raise ValidationError('output: drive-relative paths are not supported')
    for part in spelling[len(path.anchor):].split('\\'):
        if not part or part == '.':
            continue
        if (part == '..' or part.endswith(('.', ' ')) or any(ord(c) < 32 or c in '<>:"|?*' for c in part)
                or part.split('.')[0].rstrip(' ').upper() in _RESERVED):
            raise ValidationError('output: ambiguous, reserved or traversal path components are not supported')
    return path


def _safe_path(value) -> Path:
    try:
        raw = os.fspath(value)
        _checked_spelling(raw)
        expanded = os.path.expanduser(raw)
        _checked_spelling(expanded)
        absolute = os.path.abspath(expanded)
        checked = _checked_spelling(absolute)
    except (TypeError, ValueError, RuntimeError) as exc:
        raise ValidationError('output: invalid local path: ' + str(exc)) from exc
    if not checked.drive or not checked.root:
        raise ValidationError('output: an absolute local-drive path is required')
    # Added only after syntax checks. This bypasses MAX_PATH normalization, not
    # reparse checks; all operations below use this same exact Unicode spelling.
    return Path('\\\\?\\' + absolute)


@contextmanager
def _open_directory(path: Path, api):
    # Attribute-only opens do not participate in Windows sharing checks.
    # Directory-data read access makes omitted FILE_SHARE_DELETE effective.
    handle = api.CreateFileW(str(path), _DIRECTORY_READ_ACCESS, _FILE_SHARE_READ_WRITE,
                             None, _OPEN_EXISTING, _DIRECTORY_FLAGS, None)
    if handle == _INVALID_HANDLE:
        raise _error(path)
    try:
        info = _FileInformation()
        if not api.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise _error(path)
        if info.attributes & _FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValidationError('output: reparse-point paths (including symlinks and junctions) are not supported')
        if not info.attributes & _FILE_ATTRIBUTE_DIRECTORY:
            raise ValidationError('output: expected a directory')
        # Use Python identities consistently: newer CPython versions can use
        # wider volume/file IDs than BY_HANDLE_FILE_INFORMATION. The handle
        # pins this name while lstat verifies its non-reparse directory identity.
        yield handle, _directory_identity(path)
    finally:
        if not api.CloseHandle(handle):
            raise _error(path)


@contextmanager
def _directory(path: Path):
    api = _api()
    with ExitStack() as stack:
        current = Path(path.anchor)
        # Reject mapped remote drives as well as UNC spellings. Only fixed and
        # removable local drives are admitted; unknown and optical drives fail.
        if api.GetDriveTypeW(str(current)) not in (2, 3):
            raise ValidationError('output: only local NTFS drives are supported on Windows')
        handle, _ = stack.enter_context(_open_directory(current, api))
        filesystem = ctypes.create_unicode_buffer(32)
        flags = wintypes.DWORD()
        if not api.GetVolumeInformationByHandleW(handle, None, 0, None, None, ctypes.byref(flags), filesystem, len(filesystem)):
            raise _error(current)
        if filesystem.value.upper() != 'NTFS' or not flags.value & 0x00400000:
            raise ValidationError('output: Windows composite saving requires an NTFS filesystem')
        for component in path.parts[1:]:
            current = current / component
            stack.enter_context(_open_directory(current, api))
        yield api


def _directory_identity(path: Path):
    info = os.lstat(path)
    if (info.st_file_attributes & _FILE_ATTRIBUTE_REPARSE_POINT
            or not stat.S_ISDIR(info.st_mode) or not info.st_ino):
        raise ValidationError('output: cannot establish directory ownership')
    # Never compare these with Win32 BY_HANDLE_FILE_INFORMATION identities.
    return info.st_dev, info.st_ino


def _identity(path: Path):
    info = os.lstat(path)
    if info.st_file_attributes & _FILE_ATTRIBUTE_REPARSE_POINT or not stat.S_ISREG(info.st_mode) or not info.st_ino:
        return None
    return info.st_dev, info.st_ino


def _remove_owned(path: Path, identity):
    try:
        if identity is not None and _identity(path) == identity:
            os.unlink(path)
    except FileNotFoundError:
        pass


def _stage_file(path: Path, data: bytes, owned: dict):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_BINARY, 0o600)
    try:
        info = os.fstat(fd)
        if not info.st_ino:
            raise OSError('output: cannot establish staged file ownership')
        owned[path.name] = (info.st_dev, info.st_ino)
        with os.fdopen(fd, 'wb', closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(fd)
    finally:
        # CRT descriptors may deny deletion while open. The caller cleans up
        # only after this finally, using the identity recorded before writing.
        os.close(fd)


def save(data: bytes, output):
    path = _safe_path(output)
    with _directory(path.parent):
        temporary = path.parent / ('.composite-input-' + secrets.token_hex(16))
        owned = {}
        published = None
        try:
            _stage_file(temporary, data, owned)
            if _identity(temporary) != owned[temporary.name]:
                raise ValidationError('output: staged input ownership changed')
            os.link(temporary, path)
            published = owned[temporary.name]
            _remove_owned(temporary, published)
        except BaseException:
            if published is not None:
                _remove_owned(path, published)
            raise
        finally:
            if temporary.name in owned:
                _remove_owned(temporary, owned[temporary.name])


def publish(contents: dict[str, bytes], output_dir):
    path = _safe_path(output_dir)
    with _directory(path.parent) as api:
        created_root = False
        root_identity = None
        try:
            try:
                os.mkdir(path, 0o700)
                created_root = True
                root_identity = _directory_identity(path)
            except FileExistsError:
                pass
            with _open_directory(path, api) as (_, actual):
                if created_root and actual != root_identity:
                    raise ValidationError('output: destination changed during opening')
                if os.listdir(path):
                    raise ValidationError('output: destination must be empty; existing files are never overwritten')
                _publish_in_directory(contents, path, api)
        finally:
            # All child handles have closed before removing a directory. Never
            # recursively delete, and do not remove an unverified/replaced root.
            if created_root and root_identity is not None:
                _remove_empty_directory(path, root_identity, api)


def _remove_empty_directory(path, identity, api):
    try:
        with _open_directory(path, api) as (_, actual):
            same = actual == identity
        if same:
            os.rmdir(path)
    except (OSError, ValidationError):
        pass  # nonempty/unrelated/replaced paths and persistent I/O failures stay


def _publish_in_directory(contents, path, api):
    stage = path / ('.composite-stage-' + secrets.token_hex(16))
    staged, published = {}, []
    stage_identity = None
    stage_created = False

    def cleanup_files():
        failure = None
        for name, identity in staged.items():
            try:
                _remove_owned(stage / name, identity)
            except OSError as exc:
                failure = failure or exc
        if failure is not None:
            raise failure

    try:
        os.mkdir(stage, 0o700)
        stage_created = True
        stage_identity = _directory_identity(stage)
        with _open_directory(stage, api) as (_, actual):
            if actual != stage_identity:
                raise ValidationError('output: staging directory changed during opening')
            for name, data in contents.items():
                _stage_file(stage / name, data, staged)
            if os.listdir(path) != [stage.name]:
                raise ValidationError('output: destination changed during staging')
            for name in contents:  # caller checks the exact manifest-last order
                if _identity(stage / name) != staged[name]:
                    raise ValidationError('output: staged artifact ownership changed')
                os.link(stage / name, path / name)
                published.append((name, staged[name]))
            cleanup_files()
        # Directory removal is part of success: a failure rolls back manifest.
        os.rmdir(stage)
        stage_created = False
    except BaseException:
        failure = None
        for name, identity in reversed(published):
            try:
                _remove_owned(path / name, identity)
            except OSError as exc:
                failure = failure or exc
        if failure is not None:
            raise failure
        raise
    finally:
        if stage_created and stage_identity is not None:
            # No stage handle survives here. Reopen before path-based cleanup,
            # including after a prior open failure, and reject any replacement.
            try:
                with _open_directory(stage, api) as (_, actual):
                    if actual != stage_identity:
                        raise ValidationError('output: staging directory ownership changed')
                    cleanup_files()
                os.rmdir(stage)  # only empty; preserves unrelated additions
            except (FileNotFoundError, ValidationError):
                pass
