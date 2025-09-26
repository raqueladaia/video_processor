"""
GUI Components for Brightness Adjustment Tool

This module contains the tkinter-based GUI components for the brightness and
contrast adjustment tool, including video preview, controls, and batch processing.

Author: Video Processing Project
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import numpy as np
from pathlib import Path
import sys
import threading
import time
from typing import Optional, Callable, List

# Add parent directory to path for shared module imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.file_utils import find_video_files, create_output_directory
from shared.video_utils import is_valid_video_file, get_video_info

try:
    from .brightness_analyzer import BrightnessAnalyzer
    from .video_processor import VideoProcessor
except ImportError:
    from brightness_analyzer import BrightnessAnalyzer
    from video_processor import VideoProcessor


class AdjustBrightnessGUI:
    """
    Main GUI class for the brightness adjustment tool.

    Provides a tkinter-based interface for adjusting video brightness and contrast
    with real-time preview, intelligent suggestions, and batch processing capabilities.
    """

    def __init__(self):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("Video Brightness Adjustment Tool")
        self.root.geometry("1200x900")
        self.root.resizable(True, True)

        # Initialize processing components
        self.analyzer = BrightnessAnalyzer()
        self.processor = VideoProcessor()

        # Current state variables
        self.current_video_path = None
        self.preview_frame = None
        self.is_batch_mode = False
        self.batch_video_files = []
        self.batch_output_dir = None

        # GUI control variables
        self.brightness_var = tk.IntVar(value=0)
        self.contrast_var = tk.IntVar(value=0)
        self.progress_var = tk.DoubleVar(value=0)

        # Create GUI components
        self._create_widgets()
        self._setup_bindings()

        # Configure grid weights for responsive layout
        self._configure_layout()

    def _create_widgets(self):
        """Create all GUI widgets and layout."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="Video Brightness Adjustment Tool",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # File selection frame
        self._create_file_selection_frame(main_frame)

        # Video preview frame
        self._create_preview_frame(main_frame)

        # Control frame
        self._create_control_frame(main_frame)

        # Analysis frame
        self._create_analysis_frame(main_frame)

        # Progress frame
        self._create_progress_frame(main_frame)

        # Action buttons frame
        self._create_action_frame(main_frame)

    def _create_file_selection_frame(self, parent):
        """Create file selection controls."""
        file_frame = ttk.LabelFrame(parent, text="Input Selection", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # Single video selection
        ttk.Button(file_frame, text="Select Video File",
                   command=self._select_video_file).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(file_frame, text="Select Video Directory",
                   command=self._select_video_directory).grid(row=0, column=1, padx=10)

        # Current file display
        self.current_file_label = ttk.Label(file_frame, text="No file selected",
                                            foreground="gray")
        self.current_file_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))

    def _create_preview_frame(self, parent):
        """Create video preview display."""
        preview_frame = ttk.LabelFrame(parent, text="Video Preview (30 seconds)", padding="10")
        preview_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Preview canvas - increased size for better visibility
        self.preview_canvas = tk.Canvas(preview_frame, width=800, height=450, bg="black")
        self.preview_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Preview info
        self.preview_info_label = ttk.Label(preview_frame,
                                            text="Select a video file to see preview",
                                            foreground="gray")
        self.preview_info_label.grid(row=1, column=0, pady=(10, 0))

    def _create_control_frame(self, parent):
        """Create brightness and contrast control sliders."""
        control_frame = ttk.LabelFrame(parent, text="Adjustments", padding="10")
        control_frame.grid(row=2, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0), pady=(0, 10))

        # Brightness control
        ttk.Label(control_frame, text="Brightness:").grid(row=0, column=0, sticky=tk.W)
        self.brightness_scale = ttk.Scale(control_frame, from_=-100, to=100,
                                          variable=self.brightness_var,
                                          orient=tk.HORIZONTAL, length=200,
                                          command=self._on_adjustment_change)
        self.brightness_scale.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 10))

        self.brightness_value_label = ttk.Label(control_frame, text="0")
        self.brightness_value_label.grid(row=1, column=1, padx=(10, 0))

        # Contrast control
        ttk.Label(control_frame, text="Contrast:").grid(row=2, column=0, sticky=tk.W)
        self.contrast_scale = ttk.Scale(control_frame, from_=-100, to=100,
                                        variable=self.contrast_var,
                                        orient=tk.HORIZONTAL, length=200,
                                        command=self._on_adjustment_change)
        self.contrast_scale.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(5, 10))

        self.contrast_value_label = ttk.Label(control_frame, text="0")
        self.contrast_value_label.grid(row=3, column=1, padx=(10, 0))

        # Reset button
        ttk.Button(control_frame, text="Reset",
                   command=self._reset_adjustments).grid(row=4, column=0, pady=(10, 0))

        # Suggest button
        ttk.Button(control_frame, text="Suggest Settings",
                   command=self._suggest_settings).grid(row=4, column=1, padx=(10, 0), pady=(10, 0))

    def _create_analysis_frame(self, parent):
        """Create analysis results display."""
        analysis_frame = ttk.LabelFrame(parent, text="Video Analysis", padding="10")
        analysis_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.analysis_text = tk.Text(analysis_frame, height=3, width=80, wrap=tk.WORD,
                                     state=tk.DISABLED, background="#f0f0f0")
        self.analysis_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Scrollbar for analysis text
        analysis_scrollbar = ttk.Scrollbar(analysis_frame, orient=tk.VERTICAL,
                                           command=self.analysis_text.yview)
        analysis_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.analysis_text.configure(yscrollcommand=analysis_scrollbar.set)

    def _create_progress_frame(self, parent):
        """Create progress display."""
        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=0, column=0, sticky=tk.W)

        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            maximum=100, length=400)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

    def _create_action_frame(self, parent):
        """Create action buttons."""
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))

        # Output directory selection
        ttk.Button(action_frame, text="Select Output Directory",
                   command=self._select_output_directory).grid(row=0, column=0, padx=(0, 10))

        self.output_dir_label = ttk.Label(action_frame, text="No output directory selected",
                                          foreground="gray")
        self.output_dir_label.grid(row=0, column=1, sticky=tk.W)

        # Processing buttons
        button_frame = ttk.Frame(action_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(button_frame, text="Process Current Video",
                   command=self._process_current_video).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(button_frame, text="Process All Videos (Batch)",
                   command=self._process_batch).grid(row=0, column=1, padx=10)

        ttk.Button(button_frame, text="Exit",
                   command=self._on_closing).grid(row=0, column=2, padx=(10, 0))

    def _configure_layout(self):
        """Configure grid weights for responsive layout."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main frame
        main_frame = self.root.children['!frame']
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=0)
        main_frame.rowconfigure(2, weight=1)

    def _setup_bindings(self):
        """Setup event bindings."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Bind slider changes
        self.brightness_var.trace('w', self._update_value_labels)
        self.contrast_var.trace('w', self._update_value_labels)

    def _select_video_file(self):
        """Handle single video file selection."""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v"),
            ("All files", "*.*")
        ]

        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=filetypes
        )

        if file_path:
            self._load_video(file_path)
            self.is_batch_mode = False
            self.batch_video_files = []

    def _select_video_directory(self):
        """Handle video directory selection."""
        directory = filedialog.askdirectory(title="Select Directory Containing Videos")

        if directory:
            video_files = find_video_files(directory, recursive=True)

            if not video_files:
                messagebox.showwarning("No Videos Found",
                                       "No video files found in the selected directory.")
                return

            self.batch_video_files = video_files
            self.is_batch_mode = True

            # Load the first video for preview
            self._load_video(video_files[0])

            # Update display
            self.current_file_label.config(
                text=f"Directory: {directory} ({len(video_files)} videos found)",
                foreground="blue"
            )

    def _load_video(self, video_path: str):
        """Load a video for preview and analysis."""
        try:
            # Validate video file
            if not is_valid_video_file(video_path):
                messagebox.showerror("Invalid File", f"The selected file is not a valid video: {video_path}")
                return

            self.current_video_path = video_path

            # Update display
            if not self.is_batch_mode:
                filename = Path(video_path).name
                self.current_file_label.config(text=f"File: {filename}", foreground="blue")

            # Create preview frame
            preview_frame = self.processor.create_preview_frame(video_path)

            if preview_frame is not None:
                # Display first frame
                self._update_preview()

                # Analyze video
                self._analyze_current_video()

                # Update preview info
                video_info = get_video_info(video_path)
                if video_info:
                    duration_str = f"{video_info['duration']:.1f}s"
                    resolution_str = video_info['resolution']
                    self.preview_info_label.config(
                        text=f"Duration: {duration_str}, Resolution: {resolution_str}",
                        foreground="black"
                    )
            else:
                messagebox.showerror("Error", f"Could not load video: {video_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Error loading video: {e}")

    def _update_preview(self):
        """Update the video preview with current adjustments."""
        if not self.current_video_path:
            return

        try:
            # Get adjusted frame
            brightness = self.brightness_var.get()
            contrast = self.contrast_var.get()

            adjusted_frame = self.processor.apply_preview_adjustments(brightness, contrast)

            if adjusted_frame is not None:
                # Convert BGR to RGB for display
                frame_rgb = cv2.cvtColor(adjusted_frame, cv2.COLOR_BGR2RGB)

                # Resize frame to fit canvas while preserving aspect ratio
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()

                if canvas_width > 1 and canvas_height > 1:  # Ensure canvas is initialized
                    frame_resized = self._resize_frame_preserve_aspect(
                        frame_rgb, canvas_width, canvas_height
                    )

                    # Convert to PIL Image and then to ImageTk
                    pil_image = Image.fromarray(frame_resized)
                    self.preview_frame = ImageTk.PhotoImage(pil_image)

                    # Update canvas
                    self.preview_canvas.delete("all")
                    self.preview_canvas.create_image(
                        canvas_width // 2, canvas_height // 2,
                        image=self.preview_frame
                    )

        except Exception as e:
            print(f"Error updating preview: {e}")

    def _analyze_current_video(self):
        """Analyze the current video and display results."""
        if not self.current_video_path:
            return

        try:
            # Run analysis in a separate thread to avoid blocking GUI
            def analyze():
                analysis = self.analyzer.analyze_video_sample(self.current_video_path)
                description = self.analyzer.get_analysis_description(analysis)

                # Update GUI in main thread
                self.root.after(0, lambda: self._display_analysis_results(analysis, description))

            threading.Thread(target=analyze, daemon=True).start()

        except Exception as e:
            self._update_analysis_text(f"Error analyzing video: {e}")

    def _display_analysis_results(self, analysis, description):
        """Display analysis results in the GUI."""
        results_text = f"Analysis: {description}\n"
        results_text += f"Average brightness: {analysis['mean_brightness']:.1f}/255\n"
        results_text += f"Contrast (RMS): {analysis['rms_contrast']:.1f}\n"
        results_text += f"Dark pixels: {analysis['dark_pixels_ratio']*100:.1f}%, "
        results_text += f"Bright pixels: {analysis['bright_pixels_ratio']*100:.1f}%"

        self._update_analysis_text(results_text)

    def _update_analysis_text(self, text: str):
        """Update the analysis text display."""
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(1.0, text)
        self.analysis_text.config(state=tk.DISABLED)

    def _suggest_settings(self):
        """Suggest optimal brightness and contrast settings."""
        if not self.current_video_path:
            messagebox.showwarning("No Video", "Please select a video file first.")
            return

        try:
            # Analyze video and get suggestions
            analysis = self.analyzer.analyze_video_sample(self.current_video_path)
            suggestions = self.analyzer.suggest_adjustments(analysis)

            # Apply suggestions
            self.brightness_var.set(suggestions['brightness'])
            self.contrast_var.set(suggestions['contrast'])

            # Update preview
            self._update_preview()

            # Show suggestion message
            message = f"Suggested adjustments applied:\n"
            message += f"Brightness: {suggestions['brightness']:+d}\n"
            message += f"Contrast: {suggestions['contrast']:+d}"

            messagebox.showinfo("Suggestions Applied", message)

        except Exception as e:
            messagebox.showerror("Error", f"Error generating suggestions: {e}")

    def _reset_adjustments(self):
        """Reset brightness and contrast to zero."""
        self.brightness_var.set(0)
        self.contrast_var.set(0)
        self._update_preview()

    def _on_adjustment_change(self, *args):
        """Handle slider value changes."""
        self._update_preview()

    def _update_value_labels(self, *args):
        """Update the value labels next to sliders."""
        self.brightness_value_label.config(text=str(self.brightness_var.get()))
        self.contrast_value_label.config(text=str(self.contrast_var.get()))

    def _select_output_directory(self):
        """Select output directory for processed videos."""
        directory = filedialog.askdirectory(title="Select Output Directory")

        if directory:
            self.batch_output_dir = directory
            self.output_dir_label.config(text=f"Output: {directory}", foreground="blue")

    def _process_current_video(self):
        """Process the current video with applied settings."""
        if not self.current_video_path:
            messagebox.showwarning("No Video", "Please select a video file first.")
            return

        if not self.batch_output_dir:
            messagebox.showwarning("No Output Directory", "Please select an output directory first.")
            return

        # Process in separate thread
        threading.Thread(target=self._process_video_worker, args=(self.current_video_path,), daemon=True).start()

    def _process_batch(self):
        """Process all videos in batch mode."""
        if not self.is_batch_mode or not self.batch_video_files:
            messagebox.showwarning("No Batch", "Please select a video directory first.")
            return

        if not self.batch_output_dir:
            messagebox.showwarning("No Output Directory", "Please select an output directory first.")
            return

        # Confirm batch processing
        count = len(self.batch_video_files)
        brightness = self.brightness_var.get()
        contrast = self.contrast_var.get()

        message = f"Process {count} videos with these settings?\n"
        message += f"Brightness: {brightness:+d}, Contrast: {contrast:+d}"

        if messagebox.askyesno("Confirm Batch Processing", message):
            # Process in separate thread
            threading.Thread(target=self._process_batch_worker, daemon=True).start()

    def _process_video_worker(self, video_path: str):
        """Worker thread for processing a single video."""
        try:
            brightness = self.brightness_var.get()
            contrast = self.contrast_var.get()

            # Generate output path
            output_path = self.processor.generate_output_path(
                video_path, self.batch_output_dir, brightness, contrast
            )

            # Update progress
            self.root.after(0, lambda: self.progress_label.config(text=f"Processing: {Path(video_path).name}"))
            self.root.after(0, lambda: self.progress_var.set(0))

            # Progress callback
            def progress_callback(percent):
                self.root.after(0, lambda: self.progress_var.set(percent))

            # Process video
            success = self.processor.apply_brightness_contrast(
                video_path, output_path, brightness, contrast, progress_callback
            )

            # Update GUI
            if success:
                self.root.after(0, lambda: self.progress_label.config(text="Processing completed successfully"))
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Video processed successfully:\n{output_path}"))
            else:
                self.root.after(0, lambda: self.progress_label.config(text="Processing failed"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to process video: {video_path}"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error processing video: {e}"))

    def _process_batch_worker(self):
        """Worker thread for batch processing videos."""
        try:
            brightness = self.brightness_var.get()
            contrast = self.contrast_var.get()
            total_videos = len(self.batch_video_files)
            processed_count = 0

            for i, video_path in enumerate(self.batch_video_files):
                # Update overall progress
                overall_progress = (i / total_videos) * 100
                self.root.after(0, lambda p=overall_progress: self.progress_var.set(p))
                self.root.after(0, lambda v=Path(video_path).name, c=i+1, t=total_videos:
                               self.progress_label.config(text=f"Processing {c}/{t}: {v}"))

                # Generate output path
                output_path = self.processor.generate_output_path(
                    video_path, self.batch_output_dir, brightness, contrast
                )

                # Process video
                success = self.processor.apply_brightness_contrast(
                    video_path, output_path, brightness, contrast
                )

                if success:
                    processed_count += 1

            # Final update
            self.root.after(0, lambda: self.progress_var.set(100))
            self.root.after(0, lambda: self.progress_label.config(text=f"Batch processing completed: {processed_count}/{total_videos} videos processed"))

            # Show completion message
            message = f"Batch processing completed!\n"
            message += f"Successfully processed: {processed_count}/{total_videos} videos"
            self.root.after(0, lambda: messagebox.showinfo("Batch Complete", message))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error during batch processing: {e}"))

    def _resize_frame_preserve_aspect(self, frame: np.ndarray, target_width: int, target_height: int) -> np.ndarray:
        """
        Resize frame while preserving aspect ratio and adding padding if needed.

        Args:
            frame (np.ndarray): Input frame in RGB format
            target_width (int): Target canvas width
            target_height (int): Target canvas height

        Returns:
            np.ndarray: Resized frame with preserved aspect ratio
        """
        frame_height, frame_width = frame.shape[:2]

        # Calculate scaling factor to fit within target dimensions
        scale_width = target_width / frame_width
        scale_height = target_height / frame_height
        scale = min(scale_width, scale_height)

        # Calculate new dimensions
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)

        # Resize the frame
        resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # Create a black background of target size
        result = np.zeros((target_height, target_width, 3), dtype=np.uint8)

        # Calculate position to center the resized frame
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2

        # Place the resized frame in the center
        result[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_frame

        return result

    def _on_closing(self):
        """Handle application closing."""
        # Clean up resources
        self.processor.cleanup()
        self.root.quit()
        self.root.destroy()

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


if __name__ == "__main__":
    # For testing the GUI independently
    app = AdjustBrightnessGUI()
    app.run()