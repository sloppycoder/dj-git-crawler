import zipfile
from configparser import ConfigParser

import pytest
from django.conf import settings


@pytest.fixture
def crawler_conf(tmp_path):
    ini_file = f"{settings.BASE_DIR}/tests/test.ini"
    conf = ConfigParser()
    conf.read(ini_file)

    # extract test files to tmp_path directory
    with zipfile.ZipFile(f"{settings.BASE_DIR}/tests/data/repo1.zip", "r") as zip_ref:
        zip_ref.extractall(tmp_path)
    with zipfile.ZipFile(
        f"{settings.BASE_DIR}/tests/data/not_a_repo.zip", "r"
    ) as zip_ref:
        zip_ref.extractall(tmp_path)

    conf["project.local"]["local_path"] = str(tmp_path)
    yield conf
