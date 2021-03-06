from infi import unittest
from contextlib import contextmanager
from infi.mount_utils.linux import LinuxSupportedFileSystemsMixin
from mock import patch
from os.path import dirname, join
import glob

#pylint: disable-msg=W0621

class LinuxGetSupportedTestCase(unittest.TestCase):
    @contextmanager
    def patch_getters(self):
        with patch.object(LinuxSupportedFileSystemsMixin, "_get_proc_filesystems") as proc, \
             patch.object(LinuxSupportedFileSystemsMixin, "_get_etc_filesystems") as etc, \
             patch.object(LinuxSupportedFileSystemsMixin, "_is_ext4_supported") as _is_ext4_supported, \
             patch("glob.glob") as glob:
            etc.return_value = ''
            proc.return_value = ''
            glob.return_value = []
            _is_ext4_supported.return_value = False
            yield (proc, etc)

    def test_empty_list(self):
        with self.patch_getters() as (proc, etc):
            actual = LinuxSupportedFileSystemsMixin().get_supported_file_systems()
            expected = []
            self.assertEqual(set(actual), set(expected))

    def test_proc_only(self):
        with self.patch_getters() as (proc, etc):
            with open(join(dirname(__file__), "proc")) as fd:
                proc.return_value = fd.read()
            actual = LinuxSupportedFileSystemsMixin().get_supported_file_systems()
            expected = ["ext3", "iso9660"]
            self.assertEqual(set(actual), set(expected))

    def test_etc_only(self):
        with self.patch_getters() as (proc, etc):
            with open(join(dirname(__file__), "etc")) as fd:
                etc.return_value = fd.read()
            actual = LinuxSupportedFileSystemsMixin().get_supported_file_systems()
            expected = ['hfsplus', 'ext3', 'ext2', 'iso9660', 'hfs', 'vfat']
            self.assertEqual(set(actual), set(expected))

    def test_both__proc_is_empty(self):
        with self.patch_getters() as (proc, etc):
            with open(join(dirname(__file__), "etc")) as fd:
                etc.return_value = fd.read() + "\n*"
            actual = LinuxSupportedFileSystemsMixin().get_supported_file_systems()
            expected = ['hfsplus', 'ext3', 'ext2', 'iso9660', 'hfs', 'vfat']
            self.assertEqual(set(actual), set(expected))
            self.assertTrue(proc.called)

    def test_both__proc_is_same_data(self):
        with self.patch_getters() as (proc, etc):
            proc.return_value = "hfs\next3"
            with open(join(dirname(__file__), "etc")) as fd:
                etc.return_value = fd.read() + "\n*"
            actual = LinuxSupportedFileSystemsMixin().get_supported_file_systems()
            expected = ['hfsplus', 'ext3', 'ext2', 'iso9660', 'hfs', 'vfat']
            self.assertEqual(set(actual), set(expected))

    def test_both__proc_is_new_data(self):
        with self.patch_getters() as (proc, etc):
            proc.return_value = "xxx"
            with open(join(dirname(__file__), "etc")) as fd:
                etc.return_value = fd.read() + "\n*"
            actual = LinuxSupportedFileSystemsMixin().get_supported_file_systems()
            expected = ['hfsplus', 'ext3', 'ext2', 'iso9660', 'hfs', 'xxx', 'vfat']
            self.assertEqual(set(actual), set(expected))

    def test_helpers_only(self):
        import glob
        with self.patch_getters():
            with patch.object(glob, "glob") as _glob:
                _glob.return_value = ["/sbin/mount.{}".format(name) for name in ['ntfs', 'nfs', 'cifs']]
                actual = LinuxSupportedFileSystemsMixin().get_supported_file_systems()
                expected = ['ntfs', 'nfs', 'cifs']
                self.assertEqual(set(actual), set(expected))

    def test_internal_and_helpers__different_data(self):
        import glob
        with self.patch_getters() as (proc, etc):
            with patch.object(glob, "glob") as _glob:
                _glob.return_value = ["/sbin/mount.{}".format(name) for name in ['ntfs', 'nfs', 'cifs']]
                proc.return_value = "xxx"
                with open(join(dirname(__file__), "etc")) as fd:
                    etc.return_value = fd.read() + "\n*"
                actual = LinuxSupportedFileSystemsMixin().get_supported_file_systems()
                expected = ['hfsplus', 'ntfs', 'ext3', 'ext2', 'iso9660', 'hfs', 'xxx', 'nfs', 'vfat', 'cifs']
                self.assertEqual(set(actual), set(expected))

    def test_internal_and_helpers__same_data(self):
        import glob
        with patch.object(glob, "glob") as _glob:
            _glob.return_value = ["/sbin/mount.{}".format(name) for name in ['ext3', 'hfs']]
            with self.patch_getters() as (proc, etc):
                proc.return_value = "hfs\next3"
                with open(join(dirname(__file__), "etc")) as fd:
                    etc.return_value = fd.read() + "\n*"
                actual = LinuxSupportedFileSystemsMixin().get_supported_file_systems()
                expected = ['hfsplus', 'ext3', 'ext2', 'iso9660', 'hfs', 'vfat']
                self.assertEqual(set(actual), set(expected))
