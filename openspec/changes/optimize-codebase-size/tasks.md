## 1. Dependency and footprint audit

- [x] 1.1 Inventory current runtime imports and map them to `requirements.txt` entries.
- [x] 1.2 Separate runtime dependencies from packaging-only or optional build dependencies without removing current user capabilities.
- [x] 1.3 Identify large release and offline packaging assets that can be isolated from normal development and startup paths.

## 2. Codebase simplification

- [x] 2.1 Remove confirmed unused code, imports, and duplicate helpers in `core/`, `ui/`, and `utils/` while preserving behavior.
- [x] 2.2 Simplify locally redundant logic in edited modules without changing existing UI flows or export results.
- [x] 2.3 Verify that document-related modules remain covered by the retained dependency set and import graph.

## 3. Packaging and documentation alignment

- [x] 3.1 Reorganize packaging-only resources or references so daily development does not depend on release bundles.
- [x] 3.2 Update packaging and project documentation to reflect the new dependency and release resource boundaries.
- [x] 3.3 Validate that the documented Windows packaging path remains supported after the footprint reduction.
