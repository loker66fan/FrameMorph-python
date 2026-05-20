## 1. Introduce global settings infrastructure

- [x] 1.1 Create a shared application settings model for default output directory, theme, and font size persistence.
- [x] 1.2 Apply persisted theme and font size during application startup or main window initialization.
- [x] 1.3 Define supported font size presets and theme options for the settings UI.

## 2. Build and register the settings page

- [x] 2.1 Create a standalone settings page using the project’s Fluent UI patterns.
- [x] 2.2 Register the settings page in `MainWindow` as a bottom navigation item in the left primary navigation.
- [x] 2.3 Add controls for default output directory, theme switching, and application font size selection.

## 3. Remove the embedded document settings module

- [x] 3.1 Remove the internal settings module from the document workbench module navigation.
- [x] 3.2 Migrate any retained output-directory or environment-status display from the document settings module to the standalone settings page.
- [x] 3.3 Ensure document workbench behavior continues to use the shared default output configuration after the embedded settings module is removed.

## 4. Integrate and validate shared behavior

- [x] 4.1 Connect supported workflows to the shared default output directory without changing existing export behavior beyond the default location source.
- [x] 4.2 Verify that theme and font size changes apply across the main application UI.
- [x] 4.3 Validate that settings persist across relaunch and that navigation no longer exposes duplicate settings entry points.
