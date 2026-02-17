import pathlib
import sys
import tarfile

from infractl.base import RuntimeFile
from infractl.fs import prepare_to_upload, strip_file_scheme


def test_strip_file_scheme():
    if sys.platform == 'win32':
        assert strip_file_scheme('file:///C:/Windows') == 'C:/Windows'
    else:
        assert strip_file_scheme('file:///home') == '/home'
    assert strip_file_scheme('file:local') == 'local'
    assert strip_file_scheme('file:.local') == '.local'


def test_prepare_to_upload(tmp_path: pathlib.Path, set_cwd):
    current_path = tmp_path / 'current'
    working_path = tmp_path / 'working'
    runtime_path = tmp_path / 'runtime'

    current_path.mkdir()
    working_path.mkdir()
    runtime_path.mkdir()

    (current_path / 'dir1').mkdir()
    (current_path / 'dir2').mkdir()
    (current_path / 'dir2' / 'subdir1').mkdir()
    (current_path / 'dir2' / 'subdir2').mkdir()
    (current_path / 'file1').write_text('file1')
    (current_path / 'file2').write_text('file2')
    (current_path / 'dir1' / 'dir1_file1').write_text('dir1_file1')
    (current_path / 'dir2' / 'dir2_file1').write_text('dir2_file1')
    (current_path / 'dir2' / '.hidden').write_text('hidden')
    (current_path / 'dir2' / 'subdir1' / 'subdir1_file1').write_text('subdir1_file1')

    files = [
        RuntimeFile(src='file1'),
        RuntimeFile(src='file1', dst='file1.renamed'),
        RuntimeFile(src='dir1/dir1_file1'),
        RuntimeFile(src='dir1/dir1_file1', dst='dir1_file1.renamed'),
        RuntimeFile(src=str(current_path / 'file2')),
        RuntimeFile(src=str(current_path / 'file2'), dst='file2.renamed'),
        RuntimeFile(src='dir2/'),
        RuntimeFile(src='dir2/', dst='dir2/'),
        RuntimeFile(src='dir2/', dst='dir2.renamed'),  # note the missing / in dst
    ]

    with set_cwd(current_path):
        prepare_to_upload(files, working_path)

    cwd_path = working_path / 'cwd.tar'
    assert tarfile.is_tarfile(cwd_path)

    with tarfile.open(cwd_path) as cwd:
        cwd.extractall(path=runtime_path, filter='data')

    # RuntimeFile(src='file1')
    assert (runtime_path / 'file1').read_text() == 'file1'
    # RuntimeFile(src='file1', dst='file1.renamed')
    assert (runtime_path / 'file1.renamed').read_text() == 'file1'
    # RuntimeFile(src='dir1/dir1_file1')
    assert (runtime_path / 'dir1_file1').read_text() == 'dir1_file1'
    # RuntimeFile(src='dir1/dir1_file1', dst='dir1_file1.renamed')
    assert (runtime_path / 'dir1_file1.renamed').read_text() == 'dir1_file1'
    # RuntimeFile(src=str(current_path / 'file2'))
    assert (runtime_path / 'file2').read_text() == 'file2'
    # RuntimeFile(src=str(current_path / 'file2'), dst='file2.renamed')
    assert (runtime_path / 'file2.renamed').read_text() == 'file2'
    # RuntimeFile(src='dir2/')
    assert (runtime_path / '.hidden').read_text() == 'hidden'
    assert (runtime_path / 'dir2_file1').read_text() == 'dir2_file1'
    assert (runtime_path / 'subdir1').is_dir()
    assert (runtime_path / 'subdir2').is_dir()
    assert (runtime_path / 'subdir1' / 'subdir1_file1').read_text() == 'subdir1_file1'
    # RuntimeFile(src='dir2/', dst='dir2/')
    assert (runtime_path / 'dir2' / '.hidden').read_text() == 'hidden'
    assert (runtime_path / 'dir2' / 'dir2_file1').read_text() == 'dir2_file1'
    assert (runtime_path / 'dir2' / 'subdir1').is_dir()
    assert (runtime_path / 'dir2' / 'subdir2').is_dir()
    assert (runtime_path / 'dir2' / 'subdir1' / 'subdir1_file1').read_text() == 'subdir1_file1'
    # RuntimeFile(src='dir2/', dst='dir2.renamed')
    assert (runtime_path / 'dir2.renamed' / '.hidden').read_text() == 'hidden'
    assert (runtime_path / 'dir2.renamed' / 'dir2_file1').read_text() == 'dir2_file1'
    assert (runtime_path / 'dir2.renamed' / 'subdir1').is_dir()
    assert (runtime_path / 'dir2.renamed' / 'subdir2').is_dir()
    assert (
        runtime_path / 'dir2.renamed' / 'subdir1' / 'subdir1_file1'
    ).read_text() == 'subdir1_file1'
