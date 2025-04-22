import os
import re
import tkinter as tk
from tkinter import filedialog, ttk
import json
import yaml
from typing import Dict


def is_file_or_dir_exist(path: str) -> bool:
    if os.path.exists(path):
        return True
    return False


SCALE_FACTOR = 1.3


def load_cell_coordination_config(file_path: str) -> Dict:
    """
    Load the yaml config file of the cell coordination for cutting.
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
    def __init__(self, root):
        self.root = root
        self.root.title = "EEO visualizer"

        self.btn_data_select = tk.Button(root, text="Select folder", command=self.select_folder)
        self.btn_data_select.pack()

        self.btn_prev = tk.Button(root, text="Prev", command=self.prev_file)
        self.btn_prev.pack(side=tk.LEFT)

        self.btn_next = tk.Button(root, text="Next", command=self.next_file)
        self.btn_next.pack(side=tk.RIGHT)

        self.label_file = tk.Label(root, text="No file selected", font=("Arial", 12, "bold"))
        self.label_file.pack()

        self.canvas = tk.Canvas(root, width=1000, height=1000)
        self.canvas.pack(fill="both", expand = True)

        columns = (
            "Male", "Female", "White", "Black or AA", "Asian", "Native Haw", "American Indian", "Two or more",
            "F - White", "F - Black or AA", "F - Asian", "F - Native Haw", "F - American Indian", "F - Two or more",
            "Row total")


        (x_tl, y_tl, x_br, y_br) = tuple([SCALE_FACTOR * element for element in key_map["h"]["TABLE"]])
        width = x_br - x_tl
        height = y_br - y_tl
        self.frame = tk.Frame(self.canvas, width = width, height = height)
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings")
        self.tree.column("#0", width=0, stretch=tk.NO)
        print(f"Table: (x_tl, y_tl, x_br, y_br): {(x_tl, y_tl, x_br, y_br)}")

        for col in columns:
            self.tree.column(col, anchor=tk.W, width=int((x_br - x_tl) / len(columns)))
            self.tree.heading(col, text=col, anchor=tk.W)

        # self.tree.pack(fill=tk.BOTH, expand=True)
        self.canvas.create_window((x_tl, y_tl), window=self.frame, anchor="nw", width = width, height = height)

        # self.text_area = tk.Text(root, width=60, height=30, wrap=tk.WORD)
        # self.text_area.pack(pady=10)

        self.folder_path = ""
        self.files = []
        self.entry_widgets = []
        self.current_index = -1

    def extract_order(self, filename):
        match = re.search("_page_(\d+)_result.json", filename)
        return int(match.group(1)) if match else float("inf")

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            self.files = sorted([f for f in os.listdir(self.folder_path) if f.endswith(".json")],
                                key=self.extract_order)
            self.current_index = 0

            if self.files:
                self.display_file(0)
            else:
                self.label_file.config(text="No JSON files found")
                self.canvas.delete("all")
                self.tree.delete(*self.tree.get_children())
                # self.text_area.delete("1.0", tk.END)

    def build_table(self, x_tl, y_tl, width, height, table_content):
        print(f"Table: (x_tl, y_tl, x_br, y_br): {(x_tl, y_tl)}")

        for row in (table_content):
            self.tree.insert('', 'end', values=tuple(row))
        self.tree.place(x=x_tl, y=y_tl, width=width, height=2 * height)

    def parse_json_add_box(self, json_data):
        id_content_mapping = dict()
        for jitem in json_data:
            id_content_mapping[jitem["id"]] = jitem["content"]

        for section, sectionval in key_map.items():
            if section not in ["a", "b", "c", "d", "g", "h", "i"]:
                continue

            if section == "ef":
                continue
            for cell, cellval in sectionval.items():
                (x_tl, y_tl, x_br, y_br) = tuple([SCALE_FACTOR * element for element in cellval])
                if cell == "EMPLOYER NAME":
                    cell = "EMPLOYER"
                # self.canvas.create_rectangle(x_tl, y_tl, x_br, y_br, outline="black", width="2")

                result_id_chunk = f"{section}-{cell}"
                content = id_content_mapping[result_id_chunk]

                if section == "h" and cell == "TABLE":
                    self.canvas.create_rectangle(x_tl, y_tl, x_br, y_br, outline="black", width="2")
                    self.build_table(x_tl, y_tl, x_br - x_tl, y_br - y_tl, content)
                else:
                    string_content = "\n".join(content)

                    self.canvas.create_text(
                        (x_tl + x_br) / 2,
                        (y_tl + y_br) / 2,
                        text=string_content,
                        fill="black",
                        font=("Arial", 8, "bold"))

    def display_file(self, index):
        if 0 <= index < len(self.files):
            self.current_index = index
            file_path = os.path.join(self.folder_path, self.files[index])
            self.label_file.config(text=f"File: {self.files[index]}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    print(f"Reading {file_path}")
                    json_data = json.load(f)
                    # formatted_json = json.dumps(json_data, indent=4)
            except Exception as e:
                # formatted_json = f"Error reading json file: {e}"
                json_data = f"Error reading json file: {e}"
            self.canvas.delete("all")
            self.tree.delete(*self.tree.get_children())

            self.parse_json_add_box(json_data)
            # self.text_area.delete("1.0", tk.END)
            # self.text_area.insert(tk.END, formatted_json)

    def next_file(self):
        if self.current_index < len(self.files):
            self.display_file(self.current_index + 1)

    def prev_file(self):
        if self.current_index > 0:
            self.display_file(self.current_index - 1)


if __name__ == "__main__":
    root = tk.Tk()
    app = JSONFileViewer(root)
    root.mainloop()
