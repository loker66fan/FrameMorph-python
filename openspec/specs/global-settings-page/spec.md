## ADDED Requirements

### Requirement: Global settings page is available from bottom navigation
The application SHALL expose a dedicated global settings page in the left primary navigation and place its entry in the bottom navigation area instead of inside the document workbench module list.

#### Scenario: Open settings from primary navigation
- **WHEN** the user views the left primary navigation
- **THEN** the application MUST show a dedicated settings entry in the bottom navigation area

### Requirement: Document workbench no longer owns global settings navigation
The application SHALL remove the internal document workbench settings module from the document module list once the standalone settings page exists.

#### Scenario: Browse document workbench modules
- **WHEN** the user opens the document workbench module navigation
- **THEN** the module list MUST not include the former internal settings module

### Requirement: Application settings persist across launches
The application SHALL persist the selected global settings so they can be restored on the next launch.

#### Scenario: Restart after changing settings
- **WHEN** the user changes supported settings and later restarts the application
- **THEN** the application MUST restore the last saved values for those settings

### Requirement: Settings page manages default output directory
The application SHALL allow the user to view and change a default output directory from the global settings page.

#### Scenario: Change default output directory
- **WHEN** the user selects a new default output directory in the settings page
- **THEN** the application MUST save that directory as the shared default output location for supported workflows

### Requirement: Settings page manages theme selection
The application SHALL allow the user to switch the application theme from the global settings page.

#### Scenario: Change application theme
- **WHEN** the user selects a different supported theme in the settings page
- **THEN** the application MUST apply that theme to the application UI and persist the choice

### Requirement: Settings page manages application font size
The application SHALL allow the user to choose a supported application font size preset from the global settings page.

#### Scenario: Change application font size preset
- **WHEN** the user selects a different supported font size preset in the settings page
- **THEN** the application MUST apply the new UI font size and persist the choice
