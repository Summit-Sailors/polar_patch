import importlib
import logging
import shutil
from pathlib import Path

from modules.plugin_scanner import scan_plugins_in_code
from modules.ast_modifier import modify_code

# set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolarsMonkeyPatcher:
    def __init__(self, polars_module_name='polars', backup_dir='backup'):
        self.polars_module_name = polars_module_name
        self.backup_dir = Path(backup_dir)

    def _get_polars_path(self) -> Path:
        # locate the Polars library in the site-packages directory
        try:
            polars_module = importlib.import_module(self.polars_module_name)
            return Path(polars_module.__file__).parent
        except ModuleNotFoundError:
            logger.error(f"Polars module '{self.polars_module_name}' not found.")
            raise

    def _backup_polars(self, polars_path: Path):
        # backup the Polars library before making changes
        try:
            if not self.backup_dir.exists():
                self.backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = self.backup_dir / polars_path.name
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(polars_path, backup_path)
            logger.info(f"Backed up Polars library to {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup Polars library: {e}")
            raise

    def _patch_file(self, file_path: Path, plugins: list):
        # modify a file in the Polars library
        try:
            # read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # modify the code using the ASTModifier
            modified_code = modify_code(code, plugins)
            
            # write the modified code back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_code)
            logger.info(f"Patched file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to patch file {file_path}: {e}")
            raise

    def apply_patches(self):
        """Apply patches to the Polars library by scanning and modifying its code."""
        try:
            polars_path = self._get_polars_path()
            self._backup_polars(polars_path)

            # scan each Python file in the Polars library
            for py_file in polars_path.rglob('*.py'):
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()

                # scan for custom plugins
                plugins = scan_plugins_in_code(code)

                if plugins:
                    # if any custom plugins are detected, modify the code
                    self._patch_file(py_file, plugins)

            logger.info("Patching complete.")
        except Exception as e:
            logger.error(f"Failed to apply patches: {e}")

    def restore_backup(self):
        """Restore the original Polars library from the backup."""
        try:
            polars_path = self._get_polars_path()
            backup_path = self.backup_dir / polars_path.name

            if not backup_path.exists():
                logger.error(f"No backup found at {backup_path}. Cannot restore.")
                return

            shutil.rmtree(polars_path)
            shutil.copytree(backup_path, polars_path)
            logger.info(f"Restored Polars library from {backup_path}")
        except Exception as e:
            logger.error(f"Failed to restore Polars library: {e}")

# Example usage
if __name__ == "__main__":
    patcher = PolarsMonkeyPatcher()
    patcher.apply_patches()
