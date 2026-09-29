# Changelog

All notable changes to PumpCurvX are documented in this file.

## [1.5.1] - 2026-09-17

### Added

* Pump performance curve data extraction from graph images and screenshots.
* Manual X/Y graph calibration.
* Head vs Flow curve extraction.
* Efficiency vs Flow curve extraction.
* RPM-based curve identification.
* Support for multiple RPM values.
* Interactive graph visualization.
* Zoom and pan functionality.
* Point selection and editing.
* Point deletion and undo functionality.
* Pump information fields.
* Excel export.
* Save and reopen project functionality.
* Windows desktop application interface using PySide6.

### Engineering Data

* Flow values are supported across the configured application range.
* RPM values are supported across the configured application range.
* Extracted points retain their associated RPM value.

### Repository Preparation

* Verified source transferred to the Phase 2 repository.
* Verified `src/main.py` against the approved V1.5.1 development source.
* Removed machine-specific paths from the PyInstaller specification.
* Added repository-relative icon path.
* Added version metadata.
* Added pinned Python dependencies.
* Added public repository asset structure.
* Preserved diagnostic scripts in `backup/STEP_DIAGNOSTICS`.
* Added public repository documentation.

### Notes

Version 1.5.1 is the verified baseline for the Phase 2 open-source repository preparation.

OCR functionality is not part of PumpCurvX and is not planned for inclusion.

## [Unreleased]

Future development may include:

* Additional documentation.
* Automated tests.
* Repository maintenance improvements.
* Community contributions and enhancements.
