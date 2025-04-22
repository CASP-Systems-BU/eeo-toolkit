import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.doc = None
        self.current_page = None
        self.current_page_number = 0
        self.zoom = 1.0  # Initial zoom level
        self.img = None

        self.canvas = tk.Canvas(root, width=600, height=800)  # Adjust size as needed
        self.canvas.pack()

        self.coordinates_label = tk.Label(root, text="Coordinates: ")
        self.coordinates_label.pack()

        self.open_button = tk.Button(root, text="Open PDF", command=self.open_pdf)
        self.open_button.pack()
        
        # Navigation Buttons
        self.prev_button = tk.Button(root, text="Previous Page", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(root, text="Next Page", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=10)

        self.zoom_in_button = tk.Button(root, text="Zoom In", command=self.zoom_in)
        self.zoom_in_button.pack()

        self.zoom_out_button = tk.Button(root, text="Zoom Out", command=self.zoom_out)
        self.zoom_out_button.pack()

    def open_pdf(self):
        # Open file dialog to select a PDF file
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not file_path:
            return

        # Load the PDF
        self.doc = fitz.open(file_path)
        self.current_page = self.doc.load_page(0)
        self.render_page()

    def load_page(self):
        """Loads and renders the current page."""
        if self.doc and 0 <= self.current_page_number < len(self.doc):
            self.current_page = self.doc.load_page(self.current_page_number)
            self.render_page()
        else:
            print("Invalid page number")
            
    def render_page(self):
        if self.current_page is None:
            return

        # Render the page with the current zoom level
        matrix = fitz.Matrix(self.zoom, self.zoom)  # Apply zoom
        pix = self.current_page.get_pixmap(matrix=matrix)

        # Convert to Tkinter image
        self.img = tk.PhotoImage(data=pix.tobytes("ppm"))
        self.canvas.delete("all")  # Clear the canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img)

        def on_click(event):
            # Convert canvas coordinates to PDF coordinates
            x, y = event.x / self.zoom, event.y / self.zoom
            print(f"Clicked at: x={x:.2f}, y={y:.2f}")
            self.coordinates_label.config(text=f"Coordinates: x={x:.2f}, y={y:.2f}")

        # Bind click event to get coordinates
        self.canvas.bind("<Button-1>", on_click)

    def zoom_in(self):
        self.zoom *= 1.2  # Increase zoom level by 20%
        self.render_page()

    def zoom_out(self):
        self.zoom /= 1.2  # Decrease zoom level by 20%
        self.render_page()

    def next_page(self):
        """Moves to the next page if available."""
        if self.doc and self.current_page_number < len(self.doc) - 1:
            self.current_page_number += 1
            self.load_page()

    def prev_page(self):
        """Moves to the previous page if available."""
        if self.doc and self.current_page_number > 0:
            self.current_page_number -= 1
            self.load_page()

# Set up the GUI
root = tk.Tk()
root.title("PDF Coordinate Finder with Zoom")

viewer = PDFViewer(root)
root.mainloop()
