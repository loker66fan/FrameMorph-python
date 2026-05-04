# Bundled Python Installer

This folder is for the official offline Windows Python installer that can be shipped alongside the repository when the target machine has:

- no internet access
- no preinstalled Python runtime

Expected installer filename:

```text
python-3.11.9-amd64.exe
```

The build script can use this installer to create a private local Python runtime under:

```text
release/windows-portable/python-runtime/
```

This installer binary should not be committed to Git history. It is meant to be included only in offline delivery bundles.
