## ADDED Requirements

### Requirement: Default runtime dependencies remain minimal and sufficient
The project SHALL keep the default installation path limited to dependencies required for the current application runtime capabilities, while preserving existing image editing, document processing, enhancement preview, and export behavior.

#### Scenario: Install default dependencies for normal usage
- **WHEN** a developer or user installs dependencies from the default runtime dependency entrypoint
- **THEN** the application MUST still support its existing editing, document-related, preview, and export workflows without requiring build-only packages

### Requirement: Release-only resources are isolated from daily development inputs
The project SHALL organize large release artifacts, offline wheel bundles, and packaging-only inputs so they do not act as implicit requirements for normal development or application startup.

#### Scenario: Run the application without packaging resources
- **WHEN** the repository is used for normal development or local execution
- **THEN** application startup and core workflows MUST not depend on release archives or offline packaging bundles being consumed as runtime inputs

### Requirement: Code simplification preserves observable behavior
The project SHALL only apply behavior-preserving simplifications when reducing code volume, including removal of unused code, consolidation of duplicate logic, and narrower module responsibilities.

#### Scenario: Simplify internal implementation
- **WHEN** internal modules are cleaned up or reduced
- **THEN** the user-visible behavior of existing tools, dialogs, document flows, and export results MUST remain unchanged

### Requirement: Packaging workflow remains available after footprint reduction
The project SHALL preserve the documented Windows packaging workflow even if build dependencies or release assets are reorganized.

#### Scenario: Use the documented packaging flow
- **WHEN** a maintainer follows the packaging documentation after the optimization change
- **THEN** there MUST still be a supported path to prepare the Windows portable build with the required packaging resources
