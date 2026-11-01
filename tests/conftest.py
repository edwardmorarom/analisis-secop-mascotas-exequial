import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path():
    """Carpeta temporal propia: la de pytest en %TEMP% puede no ser accesible en Windows."""
    carpeta = Path(tempfile.mkdtemp(prefix="secop_test_"))
    yield carpeta
    shutil.rmtree(carpeta, ignore_errors=True)
