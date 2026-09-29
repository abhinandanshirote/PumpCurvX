# PumpCurvX

## Pump Performance Curve Data Extractor

PumpCurvX is a Windows desktop application for extracting pump performance curve data from graph images or screenshots.

The application allows users to calibrate graph axes, select curve points, review extracted data, visualize the resulting curves, and export data for further engineering analysis.

## Features

* Extract pump performance curve points from graph images or screenshots
* Manual X/Y axis calibration
* Head vs Flow curve extraction
* Efficiency vs Flow curve extraction
* RPM-based curve identification
* Support for multiple RPM values
* Interactive graph display
* Zoom and pan functionality
* Add, edit, and delete extracted points
* Undo support
* Pump information fields
* Excel data export
* Save and reopen project data
* Windows desktop interface built with PySide6

## Supported Pump Data

PumpCurvX is designed to work with common pump performance information such as:

* Flow
* Head
* Efficiency
* RPM

The application supports multiple RPM values so that data from different operating-speed curves can be retained within the project.

## Requirements

* Windows
* Python 3.12 or compatible Python 3.x environment
* PySide6 6.11.2
* pandas 3.0.5
* openpyxl 3.1.5

Install the required Python packages with:

```
pip install -r requirements.txt
```

## Running from Source

Open Command Prompt in the repository directory and run:

```
python src\main.py
```

## Project Structure

```
PumpCurvX_PHASE2_OPEN_SOURCE
|
+-- assets
|   +-- PumpCurvX.ico
|
+-- docs
|
+-- release
|
+-- src
|   +-- main.py
|   +-- PumpCurveExtractor.spec
|   +-- version_info.txt
|
+-- tests
|
+-- .gitignore
+-- README.md
+-- requirements.txt
+-- LICENSE
```

## Version

Current source version:

**PumpCurvX 1.5.1**

## Technology

PumpCurvX is developed using Python and PySide6, with pandas and openpyxl used for data processing and Excel export functionality.

## License

PumpCurvX is released under the MIT License.

See `LICENSE` for the complete license text.

## Disclaimer

PumpCurvX is an engineering data-extraction utility. Extracted values should be reviewed and validated by the user against the original pump performance documentation before being used for engineering design, operation, or other critical decisions.

## Author

**Abhinandan D. Shirote**

## Copyright

Copyright (C) 2026 ADS.

## Project Status

PumpCurvX Version 1.5.1 is the verified baseline for this Phase 2 repository preparation.

Future development may include documentation improvements, testing infrastructure, and community contributions while preserving the core application functionality.
