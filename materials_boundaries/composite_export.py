"""Conservative local export; manifest-last, not a crash-safe transaction.

On POSIX, paths are pinned with directory descriptors. Native Windows uses a
separate local-NTFS backend that locks directories and rejects reparse points. Symlink components and '..' are
refused. Files are published with exclusive hard links, never overwritten.
Ordinary exceptions roll back only files still owned by this invocation.
No guarantee is made against abrupt termination or a hostile concurrent writer.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import secrets

from .validation import ValidationError, validate_instance

ARTIFACTS = ('input.json', 'evaluation.json', 'bundle.json', 'report.txt', 'report.html', 'manifest.json')
_SAFE_DIRECTORY_SUPPORT = (all(hasattr(os, key) for key in ('O_DIRECTORY', 'O_NOFOLLOW'))
    and {os.open, os.mkdir, os.link, os.unlink, os.rmdir, os.stat}.issubset(os.supports_dir_fd)
    and os.listdir in os.supports_fd)


def json_bytes(value) -> bytes:
    from .composite import canonical_json
    return (canonical_json(value, pretty=True) + '\n').encode('utf-8')


def _safe_path(value) -> Path:
    try:
        raw = os.fspath(value)
        if not isinstance(raw, str) or not raw or '\x00' in raw:
            raise ValueError('expected a nonempty filesystem path without NUL')
        path = Path(raw).expanduser()
    except (TypeError, ValueError, RuntimeError) as exc:
        raise ValidationError('output: invalid local path: ' + str(exc)) from exc
    if '..' in path.parts:
        raise ValidationError('output: parent traversal components are not supported')
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValidationError('output: symlink paths are not supported')
    return path


@contextmanager
def _directory(path: Path):
    # Walk from the root with O_NOFOLLOW rather than following a path checked
    # earlier. Holding the final descriptor pins the selected directory.
    if not _SAFE_DIRECTORY_SUPPORT:
        raise ValidationError('output: safe directory-descriptor export is unsupported on this platform')
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in path.parts[1:]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def _identity(fd: int, name: str):
    info = os.stat(name, dir_fd=fd, follow_symlinks=False)
    return info.st_dev, info.st_ino


def _remove_owned(fd: int, name: str, identity):
    try:
        if _identity(fd, name) == identity:
            os.unlink(name, dir_fd=fd)
    except FileNotFoundError:
        pass


def _stage_file(fd: int, name: str, data: bytes):
    file_fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    identity = (os.fstat(file_fd).st_dev, os.fstat(file_fd).st_ino)
    try:
        with os.fdopen(file_fd, 'wb', closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(file_fd)
    except BaseException:
        _remove_owned(fd, name, identity)
        raise
    finally:
        os.close(file_fd)
    return identity


def save_composite_instance(instance: dict, output) -> None:
    """Publish one valid new input atomically; never overwrite an existing path."""
    validate_instance(instance)
    data = json_bytes(instance)
    if os.name == 'nt':
        from ._composite_windows import save
        return save(data, output)
    path = _safe_path(output)
    with _directory(path.parent) as parent_fd:
        temporary = '.composite-input-' + secrets.token_hex(16)
        identity = published = None
        try:
            identity = _stage_file(parent_fd, temporary, data)
            os.link(temporary, path.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd, follow_symlinks=False)
            published = identity
            _remove_owned(parent_fd, temporary, identity)
            identity = None
        except BaseException:
            if published is not None:
                _remove_owned(parent_fd, path.name, published)
            raise
        finally:
            if identity is not None:
                _remove_owned(parent_fd, temporary, identity)


def _publish_artifacts(contents: dict[str, bytes], output_dir) -> None:
    if tuple(contents) != ARTIFACTS:
        raise ValidationError('output: unexpected artifact names or order')
    if os.name == 'nt':
        from ._composite_windows import publish
        return publish(contents, output_dir)
    path = _safe_path(output_dir)
    created_root = False
    with _directory(path.parent) as parent_fd:
        try:
            os.mkdir(path.name, 0o700, dir_fd=parent_fd)
            created_root = True
        except FileExistsError:
            pass
        root_fd = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
        root_identity = (os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino)
        stage_name = '.composite-stage-' + secrets.token_hex(16)
        stage_fd = None
        stage_created = False
        published = []
        staged = []

        def cleanup_stage():
            nonlocal stage_created
            failure = None
            if stage_fd is not None:
                for name in staged:
                    try:
                        os.unlink(name, dir_fd=stage_fd)
                    except FileNotFoundError:
                        pass
                    except OSError as exc:
                        failure = failure or exc
            if stage_created:
                try:
                    os.rmdir(stage_name, dir_fd=root_fd)
                    stage_created = False
                except FileNotFoundError:
                    stage_created = False
                except OSError as exc:
                    failure = failure or exc
            if failure is not None:
                raise failure

        try:
            if os.listdir(root_fd):
                raise ValidationError('output: destination must be empty; existing files are never overwritten')
            os.mkdir(stage_name, 0o700, dir_fd=root_fd)
            stage_created = True
            stage_fd = os.open(stage_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
            for name, data in contents.items():
                staged.append(name)
                _stage_file(stage_fd, name, data)
            if os.listdir(root_fd) != [stage_name]:
                raise ValidationError('output: destination changed during staging')
            for name in ARTIFACTS:
                identity = _identity(stage_fd, name)
                os.link(name, name, src_dir_fd=stage_fd, dst_dir_fd=root_fd, follow_symlinks=False)
                published.append((name, identity))
            # Treat cleanup failure as failure too, so it cannot escape with a
            # success-marking manifest. The finally block makes one further
            # cleanup attempt after rollback; persistent I/O errors may remain.
            cleanup_stage()
        except BaseException:
            cleanup_error = None
            for name, identity in reversed(published):
                try:
                    _remove_owned(root_fd, name, identity)
                except OSError as exc:
                    cleanup_error = cleanup_error or exc
            if cleanup_error is not None:
                raise cleanup_error
            raise
        finally:
            try:
                if stage_created:
                    cleanup_stage()
            finally:
                if stage_fd is not None:
                    os.close(stage_fd)
                os.close(root_fd)
                if created_root:
                    try:
                        if _identity(parent_fd, path.name) == root_identity:
                            os.rmdir(path.name, dir_fd=parent_fd)  # empty only
                    except OSError:
                        pass


def export_composite_report(instance: dict, output_dir, *, output_unit: str = 'GPa', lang: str = 'en') -> dict:
    """Build once, render offline, then save six fixed artifacts in an empty dir.

    Returns artifact names and numerical exit status. Report replay covers the
    canonical bundle; manifest hashes independently cover saved artifact bytes.
    """
    from .composite import build_composite_report
    from .composite_render import _render_composite_report
    bundle = build_composite_report(instance, output_unit=output_unit)
    contents = {
        'input.json': json_bytes(bundle['input']),
        'evaluation.json': json_bytes(bundle['evaluation']),
        'bundle.json': json_bytes(bundle),
        'report.txt': (_render_composite_report(bundle, lang=lang, format='text') + '\n').encode('utf-8'),
        'report.html': (_render_composite_report(bundle, lang=lang, format='html') + '\n').encode('utf-8'),
    }
    manifest = {'kind': 'composite_artifact_manifest', 'schema_version': '1.0.0',
                'algorithm': 'sha256', 'files': {name: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
                                               for name, data in contents.items()},
                'scope': 'artifact_byte_integrity_only_not_authorship_or_scientific_validation'}
    contents['manifest.json'] = json_bytes(manifest)
    _publish_artifacts(contents, output_dir)
    return {'artifacts': list(ARTIFACTS), 'exit_code': 3 if any(
        row['computation'] == 'numerical_range_error' for row in bundle['evaluation']['evaluations']) else 0}
