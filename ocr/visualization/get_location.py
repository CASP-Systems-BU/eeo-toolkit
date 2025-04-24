"""
PDF Coordinate Finder with Zoom

A simple Tkinter-based PDF viewer using PyMuPDF (fitz) that allows:
- Opening a PDF document
- Navigating between pages
- Zooming in and out
- Clicking on the page to retrieve PDF coordinates
- Displaying clicked coordinates in the GUI
"""

import fitz  # PyMuPDF for PDF rendering
import tkinter as tk
from tkinter import filedialog


class PDFViewer:
    def __init__(self, root):
        """
        Initialize the PDFViewer GUI components and state variables.

        :param root: The root Tkinter window
        """
        self.root = root
        self.doc = None  # The loaded PDF document
        self.current_page = None  # The currently displayed page
        self.current_page_number = 0  # Page index (0-based)
        self.zoom = 1.0  # Current zoom level
        self.img = None  # Tkinter PhotoImage for display

        # Canvas for rendering PDF page images
        self.canvas = tk.Canvas(root, width=600, height=800)
        self.canvas.pack()

        # Label to display clicked coordinates
        self.coordinates_label = tk.Label(root, text="Coordinates: ")
        self.coordinates_label.pack()

        # Button to open a PDF file
        self.open_button = tk.Button(root, text="Open PDF", command=self.open_pdf)
        self.open_button.pack()

        # Navigation buttons for previous and next pages
        self.prev_button = tk.Button(root, text="Previous Page", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(root, text="Next Page", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=10)

        # Zoom controls
        self.zoom_in_button = tk.Button(root, text="Zoom In", command=self.zoom_in)
        self.zoom_in_button.pack()

        self.zoom_out_button = tk.Button(root, text="Zoom Out", command=self.zoom_out)
        self.zoom_out_button.pack()

    def open_pdf(self):
        """
        Open a file dialog to select a PDF file and load the first page.
        """
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not file_path:
            return

        # Load the PDF document
        self.doc = fitz.open(file_path)
        self.current_page_number = 0
        self.current_page = self.doc.load_page(self.current_page_number)
        self.render_page()

    def load_page(self):
        """
        Load and render the page at current_page_number.
        """
        if self.doc and 0 <= self.current_page_number < len(self.doc):
            self.current_page = self.doc.load_page(self.current_page_number)
            self.render_page()
        else:
            print("Invalid page number")
            # Optionally, disable navigation buttons or show a message box

    def render_page(self):
        """
        Render the current page at the current zoom level, display it on the canvas,
        and bind click events to capture coordinates.
        """
        if self.current_page is None:
            return

        # Create a transformation matrix for scaling
        matrix = fitz.Matrix(self.zoom, self.zoom)
        # Render page to a pixel map
        pix = self.current_page.get_pixmap(matrix=matrix)

        # Convert the pixmap to a Tkinter-compatible image
        self.img = tk.PhotoImage(data=pix.tobytes("ppm"))
        # Clear the canvas and draw the new image
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img)

        # Event handler for mouse clicks on the canvas
        def on_click(event):
            # Convert canvas (screen) coords back to PDF coords by dividing by zoom
            x_pdf = event.x / self.zoom
            y_pdf = event.y / self.zoom
            # Print to console for debugging
            print(f"Clicked at: x={x_pdf:.2f}, y={y_pdf:.2f}")
            # Update the label in the GUI
            self.coordinates_label.config(
                text=f"Coordinates: x={x_pdf:.2f}, y={y_pdf:.2f}"
            )

        # Bind left-click to the on_click handler
        self.canvas.bind("<Button-1>", on_click)

    def zoom_in(self):
        """
        Increase zoom level and re-render the page.
        """
        self.zoom *= 1.2  # Zoom in by 20%
        self.render_page()

    def zoom_out(self):
        """
        Decrease zoom level and re-render the page.
        """
        self.zoom /= 1.2  # Zoom out by ~17%
        self.render_page()

    def next_page(self):
        """
        Move to the next page if available and render it.
        """
        if self.doc and self.current_page_number < len(self.doc) - 1:
            self.current_page_number += 1
            self.load_page()

    def prev_page(self):
        """
        Move to the previous page if available and render it.
        """
        if self.doc and self.current_page_number > 0:
            self.current_page_number -= 1
            self.load_page()


# Entry point for launching the GUI
if __name__ == "__main__":
    root = tk.Tk()
    root.title("PDF Coordinate Finder with Zoom")
    PDFViewer(root)
    root.mainloop()
