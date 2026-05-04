# GitHub Actions Windows Build

## 1. Purpose

This workflow builds a Windows portable package of FrameMorph-python on GitHub-hosted Windows runners.

Workflow file:

- `.github/workflows/windows-portable-build.yml`

## 2. What It Does

The workflow:

1. checks out the repository
2. reads the current version from `VERSION`
3. installs Python 3.11
4. installs dependencies
5. runs PyInstaller with `release/windows-portable/FrameMorph-python.spec`
6. creates a ZIP package from `dist/FrameMorph-python/`
7. uploads the build as a GitHub Actions artifact
8. if triggered by a version tag, uploads the ZIP to the GitHub Release

## 3. Trigger Modes

### Manual trigger

You can trigger the workflow from the GitHub Actions page:

- `Actions`
- select `Windows Portable Build`
- click `Run workflow`

### Tag trigger

The workflow also runs when pushing a tag that matches:

```text
v*
```

Examples:

- `v0.1.0`
- `v0.1.1`

## 4. Output

The workflow generates:

- `dist/FrameMorph-python/`
- `dist/FrameMorph-python-windows-portable-<version>.zip`

Artifact name:

```text
FrameMorph-python-windows-portable-<version>
```

If the workflow is triggered by a tag, the ZIP is also attached to the GitHub Release.

## 5. Recommended Release Flow

1. Update `VERSION`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create and push tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

5. Wait for GitHub Actions to finish
6. Download the artifact or release ZIP

## 6. Notes

- The workflow builds on `windows-latest`
- Packaging uses one-folder mode through `release/windows-portable/FrameMorph-python.spec`
- This is more stable than one-file mode for Qt + OpenCV + external assets

## 7. Troubleshooting

### Build fails on missing dependency

Check:

- `requirements.txt`
- whether a module requires extra hidden imports

### Build succeeds but app misses models or assets

Check:

- `release/windows-portable/FrameMorph-python.spec`
- whether `assets/` and `models/` are correctly included

### Release attachment missing

Check:

- whether the workflow was triggered by a `v*` tag
- whether repository permissions allow release uploads
