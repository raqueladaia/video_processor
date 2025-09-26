"""
GUI Components for Crop Video Tool

This module contains the tkinter-based GUI components for the video cropping tool,
including interactive rectangle drawing, video preview, and crop management.

Author: Video Processing Project
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import cv2
from PIL import Image, ImageTk
import numpy as np
from pathlib import Path
import sys
import threading
from typing import Optional, List, Tuple, Dict, Any

# Add parent directory to path for shared module imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.file_utils import find_video_files, create_output_directory
from shared.video_utils import is_valid_video_file, get_video_info

try:
    from .rectangle_manager import Rectangle, RectangleManager
    from .video_processor import CropVideoProcessor
    from .crop_data import CropDataManager
except ImportError:
    from rectangle_manager import Rectangle, RectangleManager
    from video_processor import CropVideoProcessor
    from crop_data import CropDataManager


class CropVideoGUI:
    """
    Main GUI class for the video cropping tool.

    Provides an interactive interface for drawing crop rectangles on video frames,
    managing multiple crop regions, and processing videos with batch support.
    """

    def __init__(self):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("Video Crop Tool")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)

        # Initialize processing components
        self.rectangle_manager = RectangleManager()
        self.video_processor = CropVideoProcessor()
        self.crop_data_manager = CropDataManager()

        # Current state variables
        self.current_video_path = None
        self.current_frame = None
        self.is_batch_mode = False
        self.batch_video_files = []
        self.output_directory = None

        # Drawing and interaction state
        self.drawing_rectangle = False
        self.dragging_rectangle = False
        self.resizing_rectangle = False
        self.start_x = 0
        self.start_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.current_rectangle_id = None
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.resize_handle = None  # 'tl', 'tr', 'bl', 'br', 'top', 'bottom', 'left', 'right'
        self.original_rect_coords = None  # Store original coordinates for drag/resize operations

        # GUI control variables
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
        title_label = ttk.Label(main_frame, text="Video Crop Tool",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # File selection frame
        self._create_file_selection_frame(main_frame)

        # Main content area (preview and controls)
        self._create_content_area(main_frame)

        # Progress frame
        self._create_progress_frame(main_frame)

        # Action buttons frame
        self._create_action_frame(main_frame)

    def _create_file_selection_frame(self, parent):
        """Create file selection controls."""
        file_frame = ttk.LabelFrame(parent, text="Input Selection", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # Video selection buttons
        ttk.Button(file_frame, text="Select Video File",
                   command=self._select_video_file).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(file_frame, text="Select Video Directory",
                   command=self._select_video_directory).grid(row=0, column=1, padx=10)

        # Template management
        ttk.Button(file_frame, text="Load Template",
                   command=self._load_template).grid(row=0, column=2, padx=10)

        ttk.Button(file_frame, text="Save Template",
                   command=self._save_template).grid(row=0, column=3, padx=10)

        # Current file display
        self.current_file_label = ttk.Label(file_frame, text="No file selected",
                                            foreground="gray")
        self.current_file_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(10, 0))

    def _create_content_area(self, parent):
        """Create main content area with preview and controls."""
        content_frame = ttk.Frame(parent)
        content_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Video preview frame
        self._create_preview_frame(content_frame)

        # Controls frame
        self._create_controls_frame(content_frame)

    def _create_preview_frame(self, parent):
        """Create video preview and drawing canvas."""
        preview_frame = ttk.LabelFrame(parent, text="Video Preview - Draw Rectangles", padding="10")
        preview_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # Preview canvas for video and rectangle drawing
        self.preview_canvas = tk.Canvas(preview_frame, width=800, height=450, bg="black")
        self.preview_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Instructions
        instructions = ("Click and drag to draw crop rectangles.\n"
                       "Right-click on rectangles to rename or delete.\n"
                       "Rectangle names will be used for output folders.")
        instruction_label = ttk.Label(preview_frame, text=instructions,
                                     foreground="gray", font=("Arial", 9))
        instruction_label.grid(row=1, column=0, pady=(10, 0))

    def _create_controls_frame(self, parent):
        """Create controls for rectangle management."""
        controls_frame = ttk.LabelFrame(parent, text="Crop Regions", padding="10")
        controls_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Rectangle list
        list_frame = ttk.Frame(controls_frame)
        list_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Listbox with scrollbar
        self.rectangle_listbox = tk.Listbox(list_frame, height=15)
        self.rectangle_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                      command=self.rectangle_listbox.yview)
        list_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.rectangle_listbox.configure(yscrollcommand=list_scrollbar.set)

        # Rectangle management buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(button_frame, text="Rename",
                   command=self._rename_selected_rectangle).grid(row=0, column=0, padx=(0, 5))

        ttk.Button(button_frame, text="Delete",
                   command=self._delete_selected_rectangle).grid(row=0, column=1, padx=5)

        ttk.Button(button_frame, text="Clear All",
                   command=self._clear_all_rectangles).grid(row=0, column=2, padx=(5, 0))

        # Rectangle info
        self.rectangle_info_label = ttk.Label(controls_frame, text="No rectangles defined",
                                             foreground="gray")
        self.rectangle_info_label.grid(row=2, column=0, columnspan=2, pady=(10, 0))

    def _create_progress_frame(self, parent):
        """Create progress display."""
        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=0, column=0, sticky=tk.W)

        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           maximum=100, length=600)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

    def _create_action_frame(self, parent):
        """Create action buttons."""
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E))

        # Output directory selection
        output_frame = ttk.Frame(action_frame)
        output_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))

        ttk.Button(output_frame, text="Select Output Directory",
                   command=self._select_output_directory).grid(row=0, column=0, padx=(0, 10))

        self.output_dir_label = ttk.Label(output_frame, text="No output directory selected",
                                          foreground="gray")
        self.output_dir_label.grid(row=0, column=1, sticky=tk.W)

        # Processing buttons
        button_frame = ttk.Frame(action_frame)
        button_frame.grid(row=1, column=0, columnspan=3)

        ttk.Button(button_frame, text="Process Video",
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
        main_frame.rowconfigure(2, weight=1)

        # Content area
        content_frame = main_frame.children['!frame2']
        content_frame.columnconfigure(0, weight=2)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)

    def _setup_bindings(self):
        """Setup event bindings."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Canvas mouse events for rectangle drawing, dragging, and resizing
        self.preview_canvas.bind("<Button-1>", self._on_canvas_click)
        self.preview_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.preview_canvas.bind("<Button-3>", self._on_canvas_right_click)
        self.preview_canvas.bind("<Motion>", self._on_canvas_motion)

        # Rectangle list selection
        self.rectangle_listbox.bind("<<ListboxSelect>>", self._on_rectangle_select)

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

            # Update display and show warning
            self.current_file_label.config(
                text=f"Directory: {directory} ({len(video_files)} videos found)",
                foreground="blue"
            )

            # Show batch mode warning
            warning_msg = (f"Batch mode: {len(video_files)} videos found.\n\n"
                          "The same crop rectangles will be applied to ALL videos.\n"
                          "Make sure your rectangles are appropriate for all videos in the directory.")
            messagebox.showinfo("Batch Mode Warning", warning_msg)

    def _load_video(self, video_path: str):
        """Load a video for preview and cropping."""
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

            # Load first frame
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()

            if not ret:
                messagebox.showerror("Error", f"Could not read video frame: {video_path}")
                return

            self.current_frame = frame
            height, width = frame.shape[:2]

            # Update rectangle manager with video dimensions
            self.rectangle_manager.set_video_dimensions(width, height)

            # Display frame
            self._update_preview()

            # Update info display
            video_info = get_video_info(video_path)
            if video_info:
                info_text = (f"Resolution: {video_info['resolution']}, "
                           f"Duration: {video_info['duration']:.1f}s, "
                           f"FPS: {video_info['fps']:.1f}")
                self.rectangle_info_label.config(text=info_text, foreground="black")

        except Exception as e:
            messagebox.showerror("Error", f"Error loading video: {e}")

    def _update_preview(self):
        """Update the video preview with current frame and rectangles."""
        if self.current_frame is None:
            return

        try:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)

            # Calculate scale factors
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not yet initialized
                self.root.after(100, self._update_preview)
                return

            frame_height, frame_width = frame_rgb.shape[:2]

            # Calculate scale to fit canvas while preserving aspect ratio
            scale_x = canvas_width / frame_width
            scale_y = canvas_height / frame_height
            scale = min(scale_x, scale_y)

            # Calculate display dimensions
            display_width = int(frame_width * scale)
            display_height = int(frame_height * scale)

            # Resize frame
            resized_frame = cv2.resize(frame_rgb, (display_width, display_height))

            # Create centered image
            canvas_image = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
            x_offset = (canvas_width - display_width) // 2
            y_offset = (canvas_height - display_height) // 2

            canvas_image[y_offset:y_offset + display_height,
                        x_offset:x_offset + display_width] = resized_frame

            # Convert to PIL and display
            pil_image = Image.fromarray(canvas_image)
            self.photo = ImageTk.PhotoImage(pil_image)

            # Clear canvas and display image
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.photo)

            # Store scale factors for coordinate conversion
            self.scale_x = display_width / frame_width
            self.scale_y = display_height / frame_height
            self.offset_x = x_offset
            self.offset_y = y_offset

            # Draw rectangles
            self._draw_rectangles()

        except Exception as e:
            print(f"Error updating preview: {e}")

    def _draw_rectangles(self):
        """Draw all crop rectangles on the canvas."""
        for rect in self.rectangle_manager.rectangles:
            # Convert video coordinates to canvas coordinates
            canvas_x1 = self.offset_x + rect.x * self.scale_x
            canvas_y1 = self.offset_y + rect.y * self.scale_y
            canvas_x2 = self.offset_x + rect.x2 * self.scale_x
            canvas_y2 = self.offset_y + rect.y2 * self.scale_y

            # Draw rectangle
            outline_color = rect.color
            fill_color = rect.color if rect.selected else ""
            width = 3 if rect.selected else 2

            rect_id = self.preview_canvas.create_rectangle(
                canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                outline=outline_color, fill=fill_color, width=width,
                stipple="gray50" if rect.selected else ""
            )

            # Draw label
            label_x = canvas_x1 + 5
            label_y = canvas_y1 + 5
            self.preview_canvas.create_text(
                label_x, label_y, text=rect.name, fill="white",
                font=("Arial", 10, "bold"), anchor="nw"
            )

            # Draw resize handles for selected rectangle
            if rect.selected:
                self._draw_resize_handles(canvas_x1, canvas_y1, canvas_x2, canvas_y2)

    def _draw_resize_handles(self, canvas_x1: float, canvas_y1: float,
                           canvas_x2: float, canvas_y2: float):
        """Draw resize handles for the selected rectangle."""
        handle_size = 6  # Size of resize handles in pixels
        handle_color = "white"
        handle_outline = "black"

        # Calculate handle positions
        handles = [
            (canvas_x1, canvas_y1, 'tl'),  # Top-left
            (canvas_x2, canvas_y1, 'tr'),  # Top-right
            (canvas_x1, canvas_y2, 'bl'),  # Bottom-left
            (canvas_x2, canvas_y2, 'br'),  # Bottom-right
            ((canvas_x1 + canvas_x2) / 2, canvas_y1, 'top'),    # Top center
            ((canvas_x1 + canvas_x2) / 2, canvas_y2, 'bottom'), # Bottom center
            (canvas_x1, (canvas_y1 + canvas_y2) / 2, 'left'),   # Left center
            (canvas_x2, (canvas_y1 + canvas_y2) / 2, 'right')   # Right center
        ]

        # Draw each handle
        for x, y, position in handles:
            self.preview_canvas.create_rectangle(
                x - handle_size // 2, y - handle_size // 2,
                x + handle_size // 2, y + handle_size // 2,
                fill=handle_color, outline=handle_outline, width=1
            )

    def _on_canvas_click(self, event):
        """Handle mouse click on canvas."""
        # Convert canvas coordinates to video coordinates
        video_x, video_y = self._canvas_to_video_coords(event.x, event.y)

        # Check if clicking on existing rectangle
        clicked_rect = self.rectangle_manager.get_rectangle_at_point(video_x, video_y)

        if clicked_rect:
            # Select the rectangle
            self.rectangle_manager.select_rectangle(clicked_rect)
            self._update_rectangle_list()
            self._update_preview()

            # Check if clicking on a resize handle
            handle = self._get_resize_handle(clicked_rect, video_x, video_y)

            if handle:
                # Start resizing
                self.resizing_rectangle = True
                self.resize_handle = handle
                self.original_rect_coords = (clicked_rect.x, clicked_rect.y, clicked_rect.width, clicked_rect.height)
                self.drag_start_x = video_x
                self.drag_start_y = video_y
            else:
                # Start dragging
                self.dragging_rectangle = True
                self.original_rect_coords = (clicked_rect.x, clicked_rect.y, clicked_rect.width, clicked_rect.height)
                self.drag_start_x = video_x
                self.drag_start_y = video_y
        else:
            # Start drawing new rectangle
            self.drawing_rectangle = True
            self.start_x = video_x
            self.start_y = video_y
            self.rectangle_manager.select_rectangle(None)

    def _on_canvas_drag(self, event):
        """Handle mouse drag on canvas."""
        # Convert to video coordinates
        current_x, current_y = self._canvas_to_video_coords(event.x, event.y)

        if self.drawing_rectangle:
            # Handle new rectangle drawing
            self._handle_drawing_drag(current_x, current_y)
        elif self.dragging_rectangle:
            # Handle rectangle moving
            self._handle_dragging_drag(current_x, current_y)
        elif self.resizing_rectangle:
            # Handle rectangle resizing
            self._handle_resizing_drag(current_x, current_y)

    def _handle_drawing_drag(self, current_x: int, current_y: int):
        """Handle dragging during new rectangle creation."""
        # Calculate rectangle bounds
        x1 = min(self.start_x, current_x)
        y1 = min(self.start_y, current_y)
        x2 = max(self.start_x, current_x)
        y2 = max(self.start_y, current_y)

        # Convert back to canvas coordinates for display
        canvas_x1 = self.offset_x + x1 * self.scale_x
        canvas_y1 = self.offset_y + y1 * self.scale_y
        canvas_x2 = self.offset_x + x2 * self.scale_x
        canvas_y2 = self.offset_y + y2 * self.scale_y

        # Remove previous temporary rectangle
        if self.current_rectangle_id:
            self.preview_canvas.delete(self.current_rectangle_id)

        # Draw temporary rectangle
        self.current_rectangle_id = self.preview_canvas.create_rectangle(
            canvas_x1, canvas_y1, canvas_x2, canvas_y2,
            outline="yellow", width=2, dash=(5, 5)
        )

    def _handle_dragging_drag(self, current_x: int, current_y: int):
        """Handle dragging during rectangle movement."""
        selected_rect = self.rectangle_manager.selected_rectangle
        if not selected_rect:
            return

        # Calculate movement delta
        delta_x = current_x - self.drag_start_x
        delta_y = current_y - self.drag_start_y

        # Calculate new position
        new_x = self.original_rect_coords[0] + delta_x
        new_y = self.original_rect_coords[1] + delta_y

        # Constrain to video bounds
        if hasattr(self, 'current_frame'):
            height, width = self.current_frame.shape[:2]
            new_x = max(0, min(new_x, width - selected_rect.width))
            new_y = max(0, min(new_y, height - selected_rect.height))

        # Update rectangle position
        selected_rect.move(new_x, new_y)
        self._update_preview()

    def _handle_resizing_drag(self, current_x: int, current_y: int):
        """Handle dragging during rectangle resizing."""
        selected_rect = self.rectangle_manager.selected_rectangle
        if not selected_rect or not self.resize_handle:
            return

        # Get original coordinates
        orig_x, orig_y, orig_width, orig_height = self.original_rect_coords

        # Calculate movement delta
        delta_x = current_x - self.drag_start_x
        delta_y = current_y - self.drag_start_y

        # Apply resize based on handle
        new_x, new_y = orig_x, orig_y
        new_width, new_height = orig_width, orig_height

        if self.resize_handle == 'tl':  # Top-left corner
            new_x = orig_x + delta_x
            new_y = orig_y + delta_y
            new_width = orig_width - delta_x
            new_height = orig_height - delta_y
        elif self.resize_handle == 'tr':  # Top-right corner
            new_y = orig_y + delta_y
            new_width = orig_width + delta_x
            new_height = orig_height - delta_y
        elif self.resize_handle == 'bl':  # Bottom-left corner
            new_x = orig_x + delta_x
            new_width = orig_width - delta_x
            new_height = orig_height + delta_y
        elif self.resize_handle == 'br':  # Bottom-right corner
            new_width = orig_width + delta_x
            new_height = orig_height + delta_y
        elif self.resize_handle == 'top':  # Top edge
            new_y = orig_y + delta_y
            new_height = orig_height - delta_y
        elif self.resize_handle == 'bottom':  # Bottom edge
            new_height = orig_height + delta_y
        elif self.resize_handle == 'left':  # Left edge
            new_x = orig_x + delta_x
            new_width = orig_width - delta_x
        elif self.resize_handle == 'right':  # Right edge
            new_width = orig_width + delta_x

        # Enforce minimum size
        min_size = 10
        if new_width < min_size:
            if self.resize_handle in ('tl', 'bl', 'left'):
                new_x = orig_x + orig_width - min_size
            new_width = min_size
        if new_height < min_size:
            if self.resize_handle in ('tl', 'tr', 'top'):
                new_y = orig_y + orig_height - min_size
            new_height = min_size

        # Constrain to video bounds
        if hasattr(self, 'current_frame'):
            height, width = self.current_frame.shape[:2]
            new_x = max(0, min(new_x, width - new_width))
            new_y = max(0, min(new_y, height - new_height))
            new_width = min(new_width, width - new_x)
            new_height = min(new_height, height - new_y)

        # Update rectangle
        selected_rect.x = new_x
        selected_rect.y = new_y
        selected_rect.width = new_width
        selected_rect.height = new_height
        self._update_preview()

    def _on_canvas_release(self, event):
        """Handle mouse release on canvas."""
        if self.drawing_rectangle:
            self._handle_drawing_release(event)
        elif self.dragging_rectangle:
            self._handle_dragging_release(event)
        elif self.resizing_rectangle:
            self._handle_resizing_release(event)

    def _handle_drawing_release(self, event):
        """Handle mouse release during new rectangle creation."""
        self.drawing_rectangle = False

        # Remove temporary rectangle
        if self.current_rectangle_id:
            self.preview_canvas.delete(self.current_rectangle_id)
            self.current_rectangle_id = None

        # Convert to video coordinates
        end_x, end_y = self._canvas_to_video_coords(event.x, event.y)

        # Calculate final rectangle
        x = min(self.start_x, end_x)
        y = min(self.start_y, end_y)
        width = abs(end_x - self.start_x)
        height = abs(end_y - self.start_y)

        # Check minimum size
        if width < 10 or height < 10:
            return

        # Add rectangle
        rect = self.rectangle_manager.add_rectangle(x, y, width, height)
        self._update_rectangle_list()
        self._update_preview()

        # Prompt for name
        self._prompt_rectangle_name(rect)

    def _handle_dragging_release(self, event):
        """Handle mouse release during rectangle movement."""
        self.dragging_rectangle = False
        self.original_rect_coords = None
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Update the rectangle list to reflect new position
        self._update_rectangle_list()

    def _handle_resizing_release(self, event):
        """Handle mouse release during rectangle resizing."""
        self.resizing_rectangle = False
        self.resize_handle = None
        self.original_rect_coords = None
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Update the rectangle list to reflect new size
        self._update_rectangle_list()

    def _on_canvas_right_click(self, event):
        """Handle right-click on canvas for context menu."""
        # Convert to video coordinates
        video_x, video_y = self._canvas_to_video_coords(event.x, event.y)

        # Check if right-clicking on rectangle
        clicked_rect = self.rectangle_manager.get_rectangle_at_point(video_x, video_y)

        if clicked_rect:
            # Show context menu
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label=f"Rename '{clicked_rect.name}'",
                                   command=lambda: self._rename_rectangle(clicked_rect))
            context_menu.add_command(label=f"Delete '{clicked_rect.name}'",
                                   command=lambda: self._delete_rectangle(clicked_rect))

            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

    def _on_canvas_motion(self, event):
        """Handle mouse motion for cursor changes and visual feedback."""
        if self.drawing_rectangle or self.dragging_rectangle or self.resizing_rectangle:
            return  # Don't change cursor during active operations

        # Don't process if no video is loaded
        if not self.current_video_path:
            return

        # Convert to video coordinates
        video_x, video_y = self._canvas_to_video_coords(event.x, event.y)

        # Find rectangle under cursor
        rect = self.rectangle_manager.get_rectangle_at_point(video_x, video_y)

        if rect:
            # Check if over a resize handle
            handle = self._get_resize_handle(rect, video_x, video_y)
            if handle:
                cursor = self._get_cursor_for_handle(handle)
            else:
                cursor = 'hand2'  # Move cursor when over rectangle body
        else:
            cursor = 'crosshair'  # Draw cursor when over empty space

        # Update canvas cursor
        self.preview_canvas.config(cursor=cursor)

    def _canvas_to_video_coords(self, canvas_x: int, canvas_y: int) -> Tuple[int, int]:
        """Convert canvas coordinates to video coordinates."""
        # Adjust for offset and scale
        video_x = max(0, int((canvas_x - self.offset_x) / self.scale_x))
        video_y = max(0, int((canvas_y - self.offset_y) / self.scale_y))

        # Clamp to video bounds
        if hasattr(self, 'current_frame'):
            height, width = self.current_frame.shape[:2]
            video_x = min(video_x, width - 1)
            video_y = min(video_y, height - 1)

        return video_x, video_y

    def _get_resize_handle(self, rect: Rectangle, video_x: int, video_y: int) -> Optional[str]:
        """
        Determine which resize handle is at the given coordinates.

        Args:
            rect (Rectangle): Rectangle to check
            video_x (int): X coordinate in video space
            video_y (int): Y coordinate in video space

        Returns:
            Optional[str]: Handle identifier ('tl', 'tr', 'bl', 'br', 'top', 'bottom', 'left', 'right') or None
        """
        handle_size = 8  # Size of resize handles in pixels (in video space)

        # Convert handle size from canvas to video coordinates
        handle_size_video = int(handle_size / min(self.scale_x, self.scale_y))

        # Check corner handles first (higher priority)
        if abs(video_x - rect.x) <= handle_size_video and abs(video_y - rect.y) <= handle_size_video:
            return 'tl'  # Top-left
        elif abs(video_x - rect.x2) <= handle_size_video and abs(video_y - rect.y) <= handle_size_video:
            return 'tr'  # Top-right
        elif abs(video_x - rect.x) <= handle_size_video and abs(video_y - rect.y2) <= handle_size_video:
            return 'bl'  # Bottom-left
        elif abs(video_x - rect.x2) <= handle_size_video and abs(video_y - rect.y2) <= handle_size_video:
            return 'br'  # Bottom-right

        # Check edge handles
        elif abs(video_y - rect.y) <= handle_size_video and rect.x < video_x < rect.x2:
            return 'top'
        elif abs(video_y - rect.y2) <= handle_size_video and rect.x < video_x < rect.x2:
            return 'bottom'
        elif abs(video_x - rect.x) <= handle_size_video and rect.y < video_y < rect.y2:
            return 'left'
        elif abs(video_x - rect.x2) <= handle_size_video and rect.y < video_y < rect.y2:
            return 'right'

        return None

    def _get_cursor_for_handle(self, handle: Optional[str]) -> str:
        """
        Get appropriate cursor for resize handle.

        Args:
            handle (Optional[str]): Handle identifier

        Returns:
            str: Cursor name for tkinter
        """
        if handle in ('tl', 'br'):
            return 'size_nw_se'
        elif handle in ('tr', 'bl'):
            return 'size_ne_sw'
        elif handle in ('top', 'bottom'):
            return 'size_ns'
        elif handle in ('left', 'right'):
            return 'size_we'
        else:
            return 'arrow'

    def _update_rectangle_list(self):
        """Update the rectangle listbox."""
        self.rectangle_listbox.delete(0, tk.END)

        for i, rect in enumerate(self.rectangle_manager.rectangles):
            display_text = f"{rect.name} ({rect.width}x{rect.height} at {rect.x},{rect.y})"
            self.rectangle_listbox.insert(tk.END, display_text)

            # Highlight selected rectangle
            if rect.selected:
                self.rectangle_listbox.selection_set(i)

        # Update info label
        count = len(self.rectangle_manager.rectangles)
        if count == 0:
            self.rectangle_info_label.config(text="No rectangles defined", foreground="gray")
        else:
            self.rectangle_info_label.config(
                text=f"{count} crop region{'s' if count != 1 else ''} defined",
                foreground="black"
            )

    def _on_rectangle_select(self, event):
        """Handle rectangle selection from listbox."""
        selection = self.rectangle_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.rectangle_manager.rectangles):
                rect = self.rectangle_manager.rectangles[index]
                self.rectangle_manager.select_rectangle(rect)
                self._update_preview()

    def _prompt_rectangle_name(self, rectangle: Rectangle):
        """Prompt user to name a rectangle."""
        name = simpledialog.askstring(
            "Rectangle Name",
            f"Enter name for crop region:",
            initialvalue=rectangle.name
        )

        if name:
            self.rectangle_manager.rename_rectangle(rectangle, name)
            self._update_rectangle_list()
            self._update_preview()

    def _rename_selected_rectangle(self):
        """Rename the selected rectangle."""
        selected = self.rectangle_manager.selected_rectangle
        if selected:
            self._prompt_rectangle_name(selected)

    def _rename_rectangle(self, rectangle: Rectangle):
        """Rename a specific rectangle."""
        self._prompt_rectangle_name(rectangle)

    def _delete_selected_rectangle(self):
        """Delete the selected rectangle."""
        selected = self.rectangle_manager.selected_rectangle
        if selected:
            self._delete_rectangle(selected)

    def _delete_rectangle(self, rectangle: Rectangle):
        """Delete a specific rectangle."""
        if messagebox.askyesno("Confirm Delete", f"Delete crop region '{rectangle.name}'?"):
            self.rectangle_manager.remove_rectangle(rectangle)
            self._update_rectangle_list()
            self._update_preview()

    def _clear_all_rectangles(self):
        """Clear all rectangles after confirmation."""
        if self.rectangle_manager.rectangles:
            if messagebox.askyesno("Confirm Clear", "Delete all crop regions?"):
                self.rectangle_manager.clear_all()
                self._update_rectangle_list()
                self._update_preview()

    def _load_template(self):
        """Load crop rectangles from a template file."""
        templates = self.crop_data_manager.list_templates()

        if not templates:
            messagebox.showinfo("No Templates", "No saved templates found.")
            return

        # Show template selection dialog
        template_dialog = TemplateSelectionDialog(self.root, templates, "Load Template")
        template_name = template_dialog.result

        if template_name:
            rectangles = self.crop_data_manager.load_template(template_name)
            if rectangles:
                self.rectangle_manager.rectangles = rectangles
                self._update_rectangle_list()
                self._update_preview()
                messagebox.showinfo("Template Loaded", f"Loaded {len(rectangles)} crop regions from template '{template_name}'")

    def _save_template(self):
        """Save current crop rectangles as a template."""
        if not self.rectangle_manager.rectangles:
            messagebox.showwarning("No Rectangles", "No crop regions defined to save.")
            return

        template_name = simpledialog.askstring(
            "Save Template",
            "Enter template name:"
        )

        if template_name:
            video_info = None
            if self.current_video_path:
                video_info = get_video_info(self.current_video_path)

            success = self.crop_data_manager.save_as_template(
                self.rectangle_manager.rectangles, template_name, video_info
            )

            if success:
                messagebox.showinfo("Template Saved", f"Template '{template_name}' saved successfully!")

    def _select_output_directory(self):
        """Select output directory for processed videos."""
        directory = filedialog.askdirectory(title="Select Output Directory")

        if directory:
            self.output_directory = directory
            self.output_dir_label.config(text=f"Output: {directory}", foreground="blue")

    def _process_current_video(self):
        """Process the current video with defined crop regions."""
        if not self._validate_processing_setup():
            return

        # Process in separate thread
        threading.Thread(target=self._process_video_worker, args=(self.current_video_path,), daemon=True).start()

    def _process_batch(self):
        """Process all videos in batch mode."""
        if not self.is_batch_mode or not self.batch_video_files:
            messagebox.showwarning("No Batch", "Please select a video directory first.")
            return

        if not self._validate_processing_setup():
            return

        # Confirm batch processing
        count = len(self.batch_video_files)
        rect_count = len(self.rectangle_manager.rectangles)

        message = (f"Process {count} videos with {rect_count} crop regions?\n\n"
                  f"This will create {count * rect_count} output videos.")

        if messagebox.askyesno("Confirm Batch Processing", message):
            # Process in separate thread
            threading.Thread(target=self._process_batch_worker, daemon=True).start()

    def _validate_processing_setup(self) -> bool:
        """Validate that everything is ready for processing."""
        if not self.current_video_path:
            messagebox.showwarning("No Video", "Please select a video file first.")
            return False

        if not self.rectangle_manager.rectangles:
            messagebox.showwarning("No Crop Regions", "Please define at least one crop region.")
            return False

        if not self.output_directory:
            messagebox.showwarning("No Output Directory", "Please select an output directory.")
            return False

        # Validate rectangles
        errors = self.rectangle_manager.validate_all_rectangles()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return False

        return True

    def _process_video_worker(self, video_path: str):
        """Worker thread for processing a single video."""
        try:
            def progress_callback(message: str, percent: float):
                self.root.after(0, lambda: self.progress_label.config(text=message))
                self.root.after(0, lambda: self.progress_var.set(percent))

            progress_callback("Starting video processing...", 0)

            results = self.video_processor.crop_single_video(
                video_path, self.rectangle_manager.rectangles,
                self.output_directory, progress_callback
            )

            # Show results
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)

            message = f"Processing completed!\n"
            message += f"Successfully processed: {success_count}/{total_count} crop regions"

            self.root.after(0, lambda: messagebox.showinfo("Processing Complete", message))
            self.root.after(0, lambda: self.progress_label.config(text="Ready"))
            self.root.after(0, lambda: self.progress_var.set(0))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Processing Error", f"Error processing video: {e}"))

    def _process_batch_worker(self):
        """Worker thread for batch processing videos."""
        try:
            def progress_callback(message: str, percent: float):
                self.root.after(0, lambda: self.progress_label.config(text=message))
                self.root.after(0, lambda: self.progress_var.set(percent))

            progress_callback("Starting batch processing...", 0)

            results = self.video_processor.crop_video_batch(
                self.batch_video_files, self.rectangle_manager.rectangles,
                self.output_directory, progress_callback
            )

            # Calculate success statistics
            total_videos = len(results)
            total_regions = sum(len(video_results) for video_results in results.values())
            successful_regions = sum(
                sum(1 for success in video_results.values() if success)
                for video_results in results.values()
            )

            message = f"Batch processing completed!\n"
            message += f"Videos processed: {total_videos}\n"
            message += f"Crop regions processed: {successful_regions}/{total_regions}"

            self.root.after(0, lambda: messagebox.showinfo("Batch Complete", message))
            self.root.after(0, lambda: self.progress_label.config(text="Ready"))
            self.root.after(0, lambda: self.progress_var.set(0))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Batch Error", f"Error during batch processing: {e}"))

    def _on_closing(self):
        """Handle application closing."""
        # Clean up resources
        self.video_processor.cleanup()
        self.root.quit()
        self.root.destroy()

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


class TemplateSelectionDialog:
    """Dialog for selecting from available templates."""

    def __init__(self, parent, templates: List[str], title: str):
        """Initialize template selection dialog."""
        self.result = None

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        # Create widgets
        ttk.Label(self.dialog, text="Select a template:").pack(pady=10)

        # Template listbox
        self.listbox = tk.Listbox(self.dialog)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        for template in templates:
            self.listbox.insert(tk.END, template)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Load", command=self._load_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.LEFT, padx=5)

        # Bind double-click
        self.listbox.bind("<Double-Button-1>", lambda e: self._load_selected())

        # Wait for dialog
        self.dialog.wait_window()

    def _load_selected(self):
        """Load the selected template."""
        selection = self.listbox.curselection()
        if selection:
            self.result = self.listbox.get(selection[0])
        self.dialog.destroy()

    def _cancel(self):
        """Cancel template selection."""
        self.dialog.destroy()


if __name__ == "__main__":
    # For testing the GUI independently
    app = CropVideoGUI()
    app.run()