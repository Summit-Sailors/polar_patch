import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
from modules.monkey_patcher import PolarsMonkeyPatcher

class TestPolarsMonkeyPatcher(unittest.TestCase):

    @patch('modules.monkey_patcher.importlib.import_module')
    @patch('modules.monkey_patcher.scan_plugins_in_code')
    @patch('modules.monkey_patcher.modify_code')
    @patch.object(Path, 'exists', return_value=True)  # ensure the backup directory exists
    @patch.object(Path, 'mkdir')  # mock mkdir to avoid actual directory creation
    @patch('shutil.copytree')  # mock copytree to prevent actual file operations
    def test_apply_patches(self, mock_copytree, mock_mkdir, mock_exists, mock_modify_code, mock_scan_plugins_in_code, mock_import_module):
        # setup mock polars module path
        mock_polars_module = MagicMock()
        mock_polars_module.__file__ = str(Path("mock_polars_path/__init__.py"))
        mock_import_module.return_value = mock_polars_module
        
        # mock scanning and modifying
        mock_scan_plugins_in_code.return_value = ['custom_function']
        mock_modify_code.return_value = "modified code"

        # initialize the monkey patcher
        patcher = PolarsMonkeyPatcher(polars_module_name='mock_polars_path')
        
        # mock the rglob (to scan files)
        with patch.object(Path, 'rglob', return_value=[Path('mock_polars_path/mock_file.py')]), \
             patch('builtins.open', unittest.mock.mock_open(read_data='def mock_function(): pass')) as mock_file:
            
            patcher.apply_patches()

            # Verify that copytree was called (indicating backup was attempted)
            mock_copytree.assert_called_once_with(Path('mock_polars_path'), Path('backup/mock_polars_path'))

            # Verify that scanning was performed
            mock_scan_plugins_in_code.assert_called_once_with('def mock_function(): pass')
            
            # Verify that modification was done
            mock_modify_code.assert_called_once_with('def mock_function(): pass', ['custom_function'])

            # Verify that the modified code was written back to the file
            mock_file().write.assert_called_once_with("modified code")

    @patch('modules.monkey_patcher.importlib.import_module')
    @patch.object(Path, 'exists', return_value=False)
    def test_restore_backup_no_backup(self, mock_exists, mock_import_module):
        patcher = PolarsMonkeyPatcher(polars_module_name='mock_polars_path')
        with self.assertLogs('modules.monkey_patcher', level='ERROR') as log:
            patcher.restore_backup()
            # Verify that the correct log message was captured
            self.assertIn("No backup found", log.output[0])

if __name__ == '__main__':
    unittest.main()
