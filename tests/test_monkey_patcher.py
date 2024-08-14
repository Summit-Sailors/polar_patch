import unittest
import subprocess
from unittest.mock import patch, MagicMock, mock_open, call
from pathlib import Path
from polar_patch.monkey_patcher import PolarsMonkeyPatcher

class TestPolarsMonkeyPatcher(unittest.TestCase):
    
    @patch('modules.monkey_patcher.importlib.import_module')
    @patch('modules.monkey_patcher.Path.rglob')
    @patch('modules.monkey_patcher.modify_code')
    @patch('builtins.open', new_callable=mock_open, read_data="original code")
    @patch('modules.monkey_patcher.scan_plugins_in_code')
    @patch('modules.monkey_patcher.PolarsMonkeyPatcher._backup_polars')
    def test_apply_patches(self, mock_backup, mock_scan, mock_open, mock_modify, mock_rglob, mock_import):
        # setup mocks
        mock_import.return_value.__file__ = "/fake/path/to/polars/__init__.py"
        mock_scan.return_value = ['custom_plugin']
        mock_modify.return_value = "modified code"
        mock_rglob.return_value = [Path('/fake/path/to/polars/file1.py')]

        # initiate the patcher
        patcher = PolarsMonkeyPatcher()
        patcher.apply_patches()

        # assertions
        mock_import.assert_called_once_with('polars')
        mock_backup.assert_called_once()
        mock_rglob.assert_called_once_with('*.py')
        mock_scan.assert_called_once_with('original code')
        mock_modify.assert_called_once_with('original code', ['custom_plugin'])
        mock_open.assert_called_with(Path('/fake/path/to/polars/file1.py'), 'w', encoding='utf-8')
        mock_open().write.assert_called_once_with('modified code')

    @patch('modules.monkey_patcher.Path.exists')
    @patch('modules.monkey_patcher.logger')
    def test_restore_backup_no_backup(self, mock_logger, mock_exists):
        # setup mocks
        mock_exists.return_value = False

        # initiate the patcher
        patcher = PolarsMonkeyPatcher()
        patcher.restore_backup()

        # assertions
        mock_exists.assert_called_once()
        mock_logger.error.assert_called_once_with(f"No backup found at {Path('backup/polars')}. Cannot restore.")

    @patch('modules.monkey_patcher.shutil.copytree')
    @patch('modules.monkey_patcher.shutil.rmtree')
    @patch('modules.monkey_patcher.Path.exists')
    @patch('modules.monkey_patcher.logger')
    @patch('modules.monkey_patcher.PolarsMonkeyPatcher._get_polars_path')
    def test_restore_backup_with_backup(self, mock_get_polars_path, mock_logger, mock_exists, mock_rmtree, mock_copytree):
        # setup mocks
        mock_get_polars_path.return_value = Path('/fake/path/to/polars')
        mock_exists.return_value = True  # simulate the existence of backup directory

        # initiate the patcher
        patcher = PolarsMonkeyPatcher()
        patcher.restore_backup()

        # assertions
        mock_exists.assert_called_once()
        mock_rmtree.assert_called_once_with(Path("/fake/path/to/polars"))
        mock_copytree.assert_called_once_with(Path('backup/polars'), Path("/fake/path/to/polars"))
        mock_logger.info.assert_called_once_with(f"Restored Polars library from {Path('backup/polars')}")

    @patch('modules.monkey_patcher.subprocess.run')
    def test_uninstall_polars(self, mock_run):
        # initiate the patcher
        patcher = PolarsMonkeyPatcher()
        patcher.uninstall_polars()

        # assertions
        mock_run.assert_called_once_with(['rye', 'remove', 'polars-lts-cpu'], check=True)

    @patch('modules.monkey_patcher.subprocess.run')
    def test_reinstall_polars(self, mock_run):
        # initiate the patcher
        patcher = PolarsMonkeyPatcher()
        patcher.reinstall_polars()

        # assertions
        mock_run.assert_called_once_with(['rye', 'install', 'polars-lts-cpu'], check=True)

    @patch('modules.monkey_patcher.importlib.import_module', side_effect=ModuleNotFoundError)
    @patch('modules.monkey_patcher.logger')
    def test_error_handling_apply_patches(self, mock_logger, mock_import):
        # initiate the patcher
        patcher = PolarsMonkeyPatcher()
        with self.assertRaises(ModuleNotFoundError):
            patcher.apply_patches()

        # assertions
        mock_import.assert_called_once_with('polars')
        mock_logger.error.assert_has_calls([
            call("Polars module 'polars' not found."),
            call("Failed to apply patches: ")
        ])

    @patch('modules.monkey_patcher.shutil.copytree', side_effect=OSError("Copy failed"))
    @patch('modules.monkey_patcher.shutil.rmtree')
    @patch('modules.monkey_patcher.Path.exists')
    @patch('modules.monkey_patcher.logger')
    @patch('modules.monkey_patcher.PolarsMonkeyPatcher._get_polars_path')
    def test_restore_backup_copytree_failure(self, mock_get_polars_path, mock_logger, mock_exists, mock_rmtree, mock_copytree):
        # setup mocks
        mock_get_polars_path.return_value = Path('/fake/path/to/polars')
        mock_exists.return_value = True  # simulate the existence of backup directory

        # initiate the patcher
        patcher = PolarsMonkeyPatcher()
        patcher.restore_backup()

        # assertions
        mock_exists.assert_called_once()
        mock_rmtree.assert_called_once_with(Path("/fake/path/to/polars"))
        mock_copytree.assert_called_once_with(Path('backup/polars'), Path("/fake/path/to/polars"))
        mock_logger.error.assert_called_once_with(f"Failed to restore Polars library: Copy failed")

    @patch('modules.monkey_patcher.subprocess.run', side_effect=subprocess.CalledProcessError(1, 'command'))
    def test_uninstall_polars_failure(self, mock_run):
        # initiate the patcher
        patcher = PolarsMonkeyPatcher()
        with self.assertRaises(subprocess.CalledProcessError):
            patcher.uninstall_polars()

        # assertions
        mock_run.assert_called_once_with(['rye', 'remove', 'polars-lts-cpu'], check=True)

    @patch('modules.monkey_patcher.subprocess.run', side_effect=subprocess.CalledProcessError(1, 'command'))
    def test_reinstall_polars_failure(self, mock_run):
        # initiate the patcher
        patcher = PolarsMonkeyPatcher()
        with self.assertRaises(subprocess.CalledProcessError):
            patcher.reinstall_polars()

        # assertions
        mock_run.assert_called_once_with(['rye', 'install', 'polars-lts-cpu'], check=True)

    @patch('modules.monkey_patcher.Path.rglob')
    @patch('modules.monkey_patcher.scan_plugins_in_code')
    def test_apply_patches_no_plugins(self, mock_scan, mock_rglob):
        # setup mocks
        mock_rglob.return_value = [Path('/fake/path/to/polars/file1.py')]
        mock_scan.return_value = []  # no plugins detected

        with patch('builtins.open', mock_open(read_data='original code')):
            # initiate the patcher
            patcher = PolarsMonkeyPatcher()
            patcher.apply_patches()

        # assertions
        mock_scan.assert_called_once_with('original code')
        mock_rglob.assert_called_once_with('*.py')
        # ensure _patch_file was not called
        with patch('modules.monkey_patcher.PolarsMonkeyPatcher._patch_file') as mock_patch_file:
            mock_patch_file.assert_not_called()

if __name__ == '__main__':
    unittest.main()
