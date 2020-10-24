import os

from stats.utils import should_ignore_path, is_remote_git_url


def test_ignore_patterns():
    # vendered Go dependencies
    assert should_ignore_path("vendor/librar/stuff/blah.go")
    assert should_ignore_path("vendor/librar/stuff/README.md")
    # binary file
    assert should_ignore_path("lib/my_stupid_jar/blah.jar")
    assert should_ignore_path("java.jar")
    # Xcode project
    assert should_ignore_path("Accelerator.xcodeproj/project.pbxproj")
    # Cocoa pod lock
    assert should_ignore_path("Podfile.lock")
    assert should_ignore_path("Pods/Firebase/CoreOnly/Sources/Firebase.h")
    # yarn lock
    assert should_ignore_path("yarn.lock")
    # IDE/Editor files
    assert should_ignore_path(".vscode/settings.json")
    assert should_ignore_path(".idea/misc.xml")
    # build output
    assert should_ignore_path("target/output/pom.xml")
    # backkup files
    assert should_ignore_path("src/pom.xml.bak")
    # go module
    assert should_ignore_path("go.sum")

    assert not should_ignore_path("src/main/my/company/package/Application.java")
    assert not should_ignore_path("src/resources/application.yaml")
    assert not should_ignore_path("idea/misc.xml")
    assert not should_ignore_path("vscode/settings.json")


def test_load_crawler_conf(crawler_conf):
    assert "project.local" in crawler_conf.sections()
    assert os.path.isdir(crawler_conf["project.local"]["local_path"])


def test_git_repo_patterns():
    assert is_remote_git_url("https://gitlab.com/someuser/some_repo.git")
    assert is_remote_git_url("http://myserver/something.git")
    assert is_remote_git_url("git@gitlab.com:user/repo.git")
    assert is_remote_git_url("ssh://git@innersource.accenture.com/~user1/stuff.git")
    # url does not end with ".git" are not considered valid
    assert not is_remote_git_url("https://gitlab.com/someuser")
    assert not is_remote_git_url("http://myserver/something")
    assert not is_remote_git_url("git@gitlab.com:user/repo")
    # local file path is not remote
    assert not is_remote_git_url("some/local/path.git")
