"""
EEO JSON Visualizer

A Tkinter-based application to browse OCR-extracted JSON results for EEO forms.
Features:
- Select a folder containing result JSON files
- Navigate between pages (Prev/Next)
- Render bounding boxes and text overlays for form fields
- Display tabular data in a Treeview widget
"""

import os
import re
import tkinter as tk
from tkinter import filedialog, ttk
import json
import yaml
from typing import Dict

# Scale factor used to adjust coordinates from original PDF to canvas display
SCALE_FACTOR = 1.3


def is_file_or_dir_exist(path: str) -> bool:
    """
    Check if a file or directory exists at the given path.

    :param path: File or directory path to check
    :return: True if exists, False otherwise
    """
    if os.path.exists(path):
        return True
    return False


def load_cell_coordination_config(file_path: str) -> Dict:
    """
    Load a YAML configuration defining bounding box coordinates for each form cell.

    :param file_path: Path to the YAML config
    :return: Dictionary mapping section names to coordinate lists
    """
    print(f"Log: Loading {file_path}...")
    if not is_file_or_dir_exist(file_path):
        print("Error: The specified config file does not exist.")
        return

    with open(file_path, "r") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data


# Configs
form_config = "config/eeo1_typed_type1.yaml"
key_map = load_cell_coordination_config(form_config)


class JSONFileViewer:
    """
    GUI class for displaying OCR JSON output with overlays and tables.
    """

    def __init__(self, root):
        """
        Initialize the main window, controls, and canvas.

        :param root: Tkinter root window
        """
        self.root = root
        self.root.title = "EEO Visualizer"

        # Buttons for folder selection and page navigation
        self.btn_data_select = tk.Button(
            root, text="Select folder", command=self.select_folder
        )
        self.btn_data_select.pack()

        self.btn_prev = tk.Button(root, text="Prev", command=self.prev_file)
        self.btn_prev.pack(side=tk.LEFT)

        self.btn_next = tk.Button(root, text="Next", command=self.next_file)
        self.btn_next.pack(side=tk.RIGHT)

        # Label to show current file name
        self.label_file = tk.Label(
            root, text="No file selected", font=("Arial", 12, "bold")
        )
        self.label_file.pack()

        # Canvas for drawing bounding boxes and text
        self.canvas = tk.Canvas(root, width=1000, height=1000)
        self.canvas.pack(fill="both", expand=True)

        # Define table columns for section H (tabular demographic data)
        self.columns = (
            "Male",
            "Female",
            "White",
            "Black or AA",
            "Asian",
            "Native Haw",
            "American Indian",
            "Two or more",
            "F - White",
            "F - Black or AA",
            "F - Asian",
            "F - Native Haw",
            "F - American Indian",
            "F - Two or more",
            "Row total",
        )

        # Pre-calculate table bounding box from config
        x_tl, y_tl, x_br, y_br = [SCALE_FACTOR * v for v in key_map["h"]["TABLE"]]
        width = x_br - x_tl
        height = y_br - y_tl

        # Frame to host the Treeview widget
        self.frame = tk.Frame(self.canvas, width=width, height=height)
        # Create Treeview for table display
        self.tree = ttk.Treeview(self.frame, columns=self.columns, show="headings")
        self.tree.column("#0", width=0, stretch=tk.NO)

        # Configure each column width and heading
        for col in self.columns:
            self.tree.column(col, anchor=tk.W, width=int(width / len(self.columns)))
            self.tree.heading(col, text=col, anchor=tk.W)

        # Place the frame into the canvas at the correct position
        self.canvas.create_window(
            (x_tl, y_tl), window=self.frame, anchor="nw", width=width, height=height
        )

        # Initialize state
        self.folder_path = ""
        self.files = []
        self.current_index = -1

    def extract_order(self, filename: str) -> int:
        """
        Extract page order number from filename pattern: '_page_{n}_result.json'.
        """
        match = re.search(r"_page_(\d+)_result\.json", filename)
        return int(match.group(1)) if match else float("inf")

    def select_folder(self):
        """
        Prompt user to select a folder, then load sorted JSON files into state.
        """
        self.folder_path = filedialog.askdirectory()
        if not self.folder_path:
            return

        # List and sort JSON result files
        self.files = sorted(
            [f for f in os.listdir(self.folder_path) if f.endswith(".json")],
            key=self.extract_order,
        )
        self.current_index = 0

        if self.files:
            self.display_file(0)
        else:
            self.label_file.config(text="No JSON files found")
            self.canvas.delete("all")
            self.tree.delete(*self.tree.get_children())

    def build_table(
        self, x_tl: float, y_tl: float, width: float, height: float, table_content
    ):
        """
        Populate the Treeview with rows from table_content.
        """
        # Insert each row of data into the Treeview
        for row in table_content:
            self.tree.insert("", "end", values=tuple(row))
        # Position the table widget over the canvas
        self.tree.place(x=x_tl, y=y_tl, width=width, height=2 * height)

    def parse_json_add_box(self, json_data):
        """
        Draw bounding boxes and overlay text for each section/cell in the JSON.
        For section 'h' (TABLE), build a separate table.
        """
        # Map JSON items by their ID for quick lookup
        id_content_mapping = {item["id"]: item["content"] for item in json_data}

        for section, section_map in key_map.items():
            # Only process relevant sections
            if section not in ["a", "b", "c", "d", "g", "h", "i"]:
                continue

            for cell_name, coords in section_map.items():
                # Scale coordinates for display
                x_tl, y_tl, x_br, y_br = [SCALE_FACTOR * v for v in coords]
                # Normalize cell key for lookup
                lookup_id = f"{section}-{cell_name}"
                content = id_content_mapping.get(lookup_id, [])

                if section == "h" and cell_name == "TABLE":
                    # Draw table boundary and populate Treeview
                    self.canvas.create_rectangle(
                        x_tl, y_tl, x_br, y_br, outline="black", width=2
                    )
                    self.build_table(x_tl, y_tl, x_br - x_tl, y_br - y_tl, content)
                else:
                    # Join multiline text content
                    text = "\n".join(content)
                    self.canvas.create_text(
                        (x_tl + x_br) / 2,
                        (y_tl + y_br) / 2,
                        text=text,
                        fill="black",
                        font=("Arial", 8, "bold"),
                    )

    def display_file(self, index: int):
        """
        Load and display the JSON file at the given index:
        - Clear canvas and table
        - Parse JSON
        - Render overlays and table
        """
        if not (0 <= index < len(self.files)):
            return

        self.current_index = index
        file_path = os.path.join(self.folder_path, self.files[index])
        self.label_file.config(text=f"File: {self.files[index]}")

        # Read JSON content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            json_data = []

        # Clear previous drawings and table entries
        self.canvas.delete("all")
        self.tree.delete(*self.tree.get_children())

        # Render content for the current JSON
        self.parse_json_add_box(json_data)

    def next_file(self):
        """
        Move to and display the next JSON file.
        """
        if self.current_index + 1 < len(self.files):
            self.display_file(self.current_index + 1)

    def prev_file(self):
        """
        Move to and display the previous JSON file.
        """
        if self.current_index > 0:
            self.display_file(self.current_index - 1)


if __name__ == "__main__":
    # Launch the JSON File Viewer application
    root = tk.Tk()
    app = JSONFileViewer(root)
    root.mainloop()
