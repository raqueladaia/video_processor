# Video Processing Tools

A comprehensive toolkit for video processing with two main capabilities:
1. **Long Video Chopping** - Segment videos into smaller consecutive chunks
2. **Snippet Selection** - Extract specific segments around timestamps of interest

## Features

### Long Video Chopping
- Segments long videos into smaller chunks of specified duration
- Supports single video files or entire folders
- Maintains original video quality
- Never modifies original files
- Creates organized output folder structure

### Snippet Selection
- Extracts video snippets around specific timestamps
- Reads timestamp data from Excel files
- Configurable duration before/after each timestamp
- Supports videos in subdirectories
- Generates CSV reports with metadata
- Handles missing videos gracefully

## Installation

1. Clone the repository:
```bash
git clone https://github.com/raqueladaia/video_processor.git
cd video_processor
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the main program:
```bash
python main.py
```

## Requirements

- Python 3.7+
- OpenCV (cv2)
- MoviePy
- Pandas
- openpyxl
- NumPy

## Usage

### Main Interface
Run the main script to access both tools:
```bash
python main.py
```

### Long Video Chopping
Run directly:
```bash
python long_video_chopping/main.py
```

Features:
- Choose between single video or folder processing
- Specify chunk duration in seconds
- Automatic calculation of number of chunks
- Progress feedback during processing

### Snippet Selection
Run directly:
```bash
python snippet_selection/main.py
```

Features:
- Excel file parsing for timestamp data
- Flexible column name recognition
- Configurable before/after duration (default: -5s/+10s)
- Missing video handling
- Already processed video detection
- CSV report generation

## Excel File Format

For snippet selection, the Excel file should contain:

Required columns (any of these names):
- **Video names**: `video`, `video_name`, `file`, `filename`, `file_name`
- **Timestamps**: `time`, `timestamp`, `time_of_interest`, `start_time`

Optional columns:
- **Arousal type**: `arousal`, `arousal_type`, `type`, `category`
- **Comments**: `comment`, `comments`, `description`, `notes`

Timestamp formats supported:
- Seconds: `125.5`
- MM:SS: `2:05`
- HH:MM:SS: `0:02:05`

## Output Structure

### Long Video Chopping
```
output_directory/
├── video1_name/
│   ├── video1_name_001.mp4
│   ├── video1_name_002.mp4
│   └── ...
└── video2_name/
    ├── video2_name_001.mp4
    └── ...
```

### Snippet Selection
```
output_directory/
├── video1_123045_arousal_type.mp4
├── video1_124530_arousal_type.mp4
├── snippet_processing_report_YYYYMMDD_HHMMSS.csv
└── ...
```

## Project Structure

```
video_processing/
├── main.py                          # Main entry point
├── requirements.txt                 # Dependencies
├── shared/                          # Common utilities
│   ├── video_utils.py              # Video operations
│   ├── file_utils.py               # File handling
│   └── user_interface.py           # UI functions
├── long_video_chopping/            # Video chopping module
│   ├── main.py                     # Entry point
│   └── video_processor.py          # Core processing
└── snippet_selection/              # Snippet extraction module
    ├── main.py                     # Entry point
    ├── excel_parser.py             # Excel file handling
    ├── video_extractor.py          # Video extraction
    ├── csv_manager.py              # CSV reporting
    └── file_manager.py             # File discovery
```

## Error Handling

The toolkit includes comprehensive error handling:
- Input validation for all user inputs
- Video file format verification
- Missing file detection and reporting
- Progress feedback and status updates
- Graceful handling of processing errors

## Contributing

This project follows these coding principles:
- Comprehensive commenting for code understanding
- Never modify original files
- Avoid redundant code
- Reuse existing functions when possible

## License

This project is open source. Please refer to the repository for license details.

## Support

For issues and feature requests, please use the GitHub repository issue tracker.