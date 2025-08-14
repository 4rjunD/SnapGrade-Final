# Excel Export for SnapGrade

This module provides functionality to export student grading data to Excel format, allowing teachers to download and review student assessments.

## Features

- Exports batch grading results to Excel format
- Creates a summary sheet with an overview of all results
- Creates a detailed sheet with full student responses and feedback
- Safely handles complex data structures
- Auto-adjusts column widths for readability
- Provides error handling and fallbacks

## Usage

The Excel export functionality is automatically integrated with the batch grading process. When you grade multiple assignments at once, you'll see a "Download Excel Report" button in the results summary section.

## Implementation Details

- `excel_export.py` - Contains the core Excel generation logic
- `static/css/excel_export.css` - Styling for the download button
- Excel files are first created in a temporary directory (`temp_excel/`) and then copied to the exports directory when downloaded

## Troubleshooting

If you encounter issues with Excel files:

1. Check that openpyxl is properly installed (`pip install openpyxl`)
2. Check that the `temp_excel` and `exports` directories both exist and are writable
3. Look for error messages in the server logs
