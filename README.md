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
- Extracts video snippets around specific timestamps using FFmpeg
- Reads timestamp data from Excel files (supports multiple sheets)
- Configurable duration before/after each timestamp
- Supports videos in subdirectories
- Automatic animal ID extraction from video names
- Pain/non-pain classification support
- Generates CSV reports with metadata
- Handles missing videos gracefully
- Fast, lossless video extraction

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
- FFmpeg (system installation required)
- OpenCV (cv2)
- Pandas
- openpyxl
- NumPy
- Pillow

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
- **Flexible sheet selection**: Choose all sheets, specific sheets, or ranges
- Flexible column name recognition
- Forward-fills empty video name cells
- Extracts animal ID from video names (2nd underscore-separated item)
- Pain/non-pain classification from attention columns
- Configurable before/after duration (default: -5s/+10s)
- Fast FFmpeg-based extraction
- Missing video handling
- Already processed video detection
- CSV report generation

## Excel File Format

For snippet selection, the Excel file should contain:

**Sheet Selection**: The program will ask which sheets to process:
- Process all sheets at once
- Select specific sheets by number (e.g., `1`, `1,3`, `1-3`, or `all`)
- Supports individual selections, comma-separated lists, and ranges

**Video Name Matching**: The program uses intelligent matching strategies:
1. **Exact match**: Video name in Excel exactly matches file name (without extension)
2. **Partial match**: Video name in Excel is contained in file name
   - Example: Excel has `2522_2616_bs` → matches file `2522_2616_bs_recording_001.mp4`
3. **Fuzzy match**: Similar names using similarity scoring (for typos/variations)

**Supported Video Formats**: `.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv`, `.flv`, `.webm`, `.m4v`
- Works with videos that have no audio track

Required columns (any of these names):
- **Video names**: `video`, `video_name`, `file`, `filename`, `file_name`
  - Empty cells automatically inherit the value from the previous row
  - Animal ID is extracted from the 2nd underscore-separated segment (e.g., `2522_2616_bs` → animal_id: `2616`)
- **Timestamps**: `time`, `timestamp`, `time_of_interest`, `start_time`, `time_awakening_onset`

Optional columns:
- **Pain/Non-pain classification**: `arousal`, `arousal_type`, `type`, `category`, `attention_to_left_hindpaw`, `attention_to_left_paw`
  - `y` or `Y` = pain
  - `n` or `N` = nonpain
  - Empty = unclassified
- **Comments**: `comment`, `comments`, `description`, `notes`

Timestamp formats supported:
- With parentheses: `(4:52:13)` or `(10:23:45)`
- Without parentheses: `0:02:05` or `2:05`
- Seconds: `125.5`

## Use Cases

### Pain vs Non-Pain Awakenings Analysis
The snippet selection module is specifically designed for analyzing pain and non-pain awakenings in animal behavior studies:

1. **Input**: Excel file with awakening timestamps and pain/non-pain classifications
   - Supports multiple animals across different videos
   - Automatically extracts animal IDs from video filenames
   - Handles both classified and unclassified awakenings

2. **Processing**:
   - Searches recursively through video directories
   - Extracts snippets around each awakening event
   - Uses FFmpeg for fast, lossless extraction
   - Default: 5 seconds before + 10 seconds after each timestamp

3. **Output**:
   - Organized snippets with descriptive filenames
   - CSV report for tracking and analysis
   - Ready for behavioral annotation or machine learning

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
Snippets are named using the format: `{animal_id}_{pain|nonpain}_{timestamp}.{ext}`

```
output_directory/
├── 2616_pain_045213.mp4              # Animal 2616, pain awakening at 04:52:13
├── 3007_nonpain_033207.mp4           # Animal 3007, non-pain awakening at 03:32:07
├── 3008_pain_033425.mp4              # Animal 3008, pain awakening at 03:34:25
├── 2616_073607.mp4                   # Animal 2616, unclassified awakening at 07:36:07
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