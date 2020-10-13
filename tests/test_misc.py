import os

from stats.utils import should_ignore_path


def test_ignore_patterns():
    assert should_ignore_path("vendor/librar/stuff/blah.go")
    assert should_ignore_path("lib/my_stupid_jar/blah.jar")
    assert should_ignore_path("blah.jar")
    assert not should_ignore_path("src/main/my/company/package/Application.java")
    assert not should_ignore_path("src/resources/application.yaml")


def test_load_crawler_conf(crawler_conf):
    assert "project.local" in crawler_conf.sections()
    assert os.path.isdir(crawler_conf["project.local"]["local_path"])
