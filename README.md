# Video Processing Tools

A comprehensive toolkit for video processing with five main capabilities:
1. **Long Video Chopping** - Segment videos into smaller consecutive chunks
2. **Snippet Selection** - Extract specific segments around timestamps of interest
3. **Adjust Brightness** - GUI tool for adjusting video brightness and contrast
4. **Crop Video** - GUI tool for cropping videos into multiple regions
5. **Video Metadata Check** - Extract and analyze comprehensive video metadata

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

### Video Metadata Check
- Extracts comprehensive video metadata (FPS, resolution, duration, etc.)
- Compares multiple videos for consistency
- Validates videos against user-specified criteria
- Detects anomalies and outliers
- Generates reports in multiple formats (JSON, CSV, TXT)
- Supports both OpenCV and FFprobe for maximum compatibility
- Read-only operations - never modifies original files

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

## FFmpeg Installation (Windows)

This project requires FFmpeg to be installed and added to your system PATH. Follow these steps:

### Step 0: Download FFmpeg
Download FFmpeg (ffmpeg-git-full.7z) from https://www.gyan.dev/ffmpeg/builds/

### Step 1: Find and copy the FFmpeg bin folder path
1. Extract the downloaded FFmpeg archive to a location like `C:\ffmpeg`
2. Inside the extracted folder, find and open the `bin` folder
   - The full path will look something like `C:\ffmpeg\bin`
3. Copy this full path to your clipboard

### Step 2: Add the path to the environment variables
1. Press the Windows key + X and select "System"
2. Go to "Advanced system settings"
3. In the System Properties window, click on "Environment Variables"
4. Under "System variables," find and select the `Path` variable, then click "Edit"
5. Click "New" and paste the path you copied in Step 1
6. Click "OK" on all open windows to save the changes

### Step 3: Verify the installation
1. Open Command Prompt (search for `cmd` in the Start Menu)
2. Type the following command and press Enter:
```bash
ffmpeg -version
```
3. If the installation was successful, you will see the FFmpeg version information displayed

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

### Video Metadata Check
Run directly:
```bash
python video_metadata_check/main.py
```

Features:
- **Single or batch analysis**: Analyze one video or entire directories
- **Comprehensive metadata extraction**:
  - Recording frame rate (from codec)
  - Playback frame rate
  - Actual frame rate (calculated from frame count/duration)
  - Duration and length
  - Number of frames
  - Resolution (width x height)
  - File size
  - Video/audio codecs
  - Bitrate
- **Comparison mode**: Compare multiple videos for consistency
  - Select which fields to compare
  - Validate against user-specified criteria
  - Detect anomalies and outliers
- **Multiple output formats**:
  - Console output with formatted tables
  - JSON export for programmatic use
  - CSV export for spreadsheets
  - Human-readable TXT reports

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

### Video Metadata Check
Reports are generated in multiple formats with timestamped filenames:

```
output_directory/
├── video_metadata_20231115_143022.json        # Structured JSON report
├── video_metadata_20231115_143022.csv         # Spreadsheet-compatible CSV
└── video_metadata_report_20231115_143022.txt  # Human-readable text report
```

Example console output:
```
================================================================================
VIDEO METADATA REPORT
================================================================================
Total videos analyzed: 3
Report generated: 2023-11-15 14:30:22
================================================================================

[Video 1] experiment_video_001.mp4
--------------------------------------------------------------------------------
  Recording Frame Rate........... 30.00 FPS
  Playback Frame Rate............ 30.00 FPS
  Actual Frame Rate.............. 29.97 FPS
  Duration....................... 00:05:30
  Number of Frames............... 9,900
  Resolution..................... 1920x1080
  File Size...................... 245.67 MB

================================================================================
COMPARISON RESULTS
================================================================================

✓ Fields that MATCH across all videos:
  • Frame Rate (FPS): 30.00
  • Resolution: 1920x1080
  • Video Codec: h264

✗ Fields that DIFFER across videos:
  • Duration:
    - 00:05:30: 2 video(s)
    - 00:10:15: 1 video(s)
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
├── snippet_selection/              # Snippet extraction module
│   ├── main.py                     # Entry point
│   ├── excel_parser.py             # Excel file handling
│   ├── video_extractor.py          # Video extraction
│   ├── csv_manager.py              # CSV reporting
│   └── file_manager.py             # File discovery
├── adjust_brightness/              # Brightness adjustment module
│   └── main.py                     # GUI application
├── crop_video/                     # Video cropping module
│   └── main.py                     # GUI application
└── video_metadata_check/           # Video metadata analysis module
    ├── main.py                     # Entry point
    ├── metadata_extractor.py       # Metadata extraction
    ├── metadata_comparator.py      # Video comparison
    └── report_generator.py         # Report generation
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