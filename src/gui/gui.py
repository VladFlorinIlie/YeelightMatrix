import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
import logging
from yeelight_matrix.cube_matrix import CubeMatrix, CubeMatrixException
from yeelight_matrix.layout import Layout
from grid import ColorPickerGrid

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class YeelightGUI:
    def __init__(self, master):
        self.master = master
        master.title("Yeelight Cube Matrix Controller")

        self.ip = tk.StringVar(value="192.168.0.34")
        self.port = tk.IntVar(value=55443)
        self.layout_orientation = tk.StringVar(value="vertical")
        self.layout_start = tk.StringVar(value="bottom")
        self.cube = None

        self.layout = None
        self.layout_defined = False

        self.create_widgets()
        self.create_layout()  # Initialize the layout object

    def create_layout(self):
        """Creates or recreates the layout object based on UI controls."""
        if self.layout is None:
            self.layout = Layout(self.layout_orientation.get(), self.layout_start.get())
        else:
            # Recreate layout with new orientation or start position
            module_types = [module.type for module in self.layout.get_modules()]
            self.layout = Layout(self.layout_orientation.get(), self.layout_start.get())
            self.layout.add_modules_list(module_types)

        self.update_module_display()


    def create_widgets(self):
        """Creates and arranges all the widgets in the main window."""
        # Main frame
        main_frame = tk.Frame(self.master, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Connection Frame
        conn_frame = tk.LabelFrame(main_frame, text="Connection")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        tk.Label(conn_frame, text="IP Address:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(conn_frame, textvariable=self.ip).grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(conn_frame, text="Port:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(conn_frame, textvariable=self.port).grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        tk.Button(conn_frame, text="Connect", command=self.connect_to_bulb).grid(row=2, column=0, columnspan=2, pady=5)

        conn_frame.columnconfigure(1, weight=1)

        # Layout Configuration Frame
        layout_frame = tk.LabelFrame(main_frame, text="Layout Configuration")
        layout_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        tk.Label(layout_frame, text="Orientation:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        tk.Radiobutton(layout_frame, text="Vertical", variable=self.layout_orientation, value="vertical", command=self.create_layout).grid(row=0, column=1)
        tk.Radiobutton(layout_frame, text="Horizontal", variable=self.layout_orientation, value="horizontal", command=self.create_layout).grid(row=0, column=2)

        tk.Label(layout_frame, text="Layout Start:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.layout_start_option_menu = tk.OptionMenu(layout_frame, self.layout_start, "bottom", "top", "left", "right")
        self.layout_start_option_menu.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5)

        self.layout_orientation.trace_add("write", self.update_layout_start_options)

        # Module Management Frame
        self.module_frame = tk.LabelFrame(main_frame, text="Modules")
        self.module_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=5)
        main_frame.rowconfigure(2, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.module_list_frame = tk.Frame(self.module_frame)
        self.module_list_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        add_module_frame = tk.Frame(self.module_frame)
        add_module_frame.pack(pady=5)

        tk.Button(add_module_frame, text="Add 5x5 Clear", command=lambda: self.add_module("5x5_clear")).pack(side=tk.LEFT, padx=5)
        tk.Button(add_module_frame, text="Add 5x5 Blur", command=lambda: self.add_module("5x5_blur")).pack(side=tk.LEFT, padx=5)
        tk.Button(add_module_frame, text="Add 1x1", command=lambda: self.add_module("1x1")).pack(side=tk.LEFT, padx=5)

        # Send Command Frame
        send_frame = tk.Frame(main_frame)
        send_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.send_command_button = tk.Button(send_frame, text="Send Layout to Device", command=self.send_layout_command)
        self.send_command_button.pack()


    def update_layout_start_options(self, *args):
        """Updates the layout start options based on the selected orientation."""
        orientation = self.layout_orientation.get()
        menu = self.layout_start_option_menu["menu"]
        menu.delete(0, "end")
        if orientation == "vertical":
            options = ["bottom", "top"]
        else:
            options = ["left", "right"]
        for option in options:
            menu.add_command(label=option, command=lambda value=option: self.layout_start.set(value))
        self.layout_start.set(options[0])
        self.create_layout()


    def connect_to_bulb(self):
        try:
            self.cube = CubeMatrix(self.ip.get(), self.port.get())
            self.cube.set_fx_mode("direct")
            messagebox.showinfo("Success", "Connected to cube!")
            self.send_command_button.config(state=tk.NORMAL)
        except CubeMatrixException as e:
            messagebox.showerror("Error", f"Could not connect: {e}")


    def add_module(self, module_type):
        """Adds a module to the layout and updates the display."""
        if self.layout is None:
            self.create_layout()

        self.layout.add_module(module_type)
        self.update_module_display()


    def remove_module(self, module_index):
        """Removes a module from the layout and updates the display."""
        self.layout.remove_module(module_index)
        self.update_module_display()


    def set_module_colors(self, module_index):
        """Sets colors for a module, handling different module types and errors."""
        if self.layout is None:
            messagebox.showwarning("Warning", "Layout not initialized.")
            return

        module = self.layout.get_modules()[module_index]
        if module.type.startswith("5x5"):
            initial_colors = module.get_colors() or ["#000000"] * 25
            color_picker = ColorPickerGrid(
                self.master, module_index, initial_colors,
                lambda colors: self.on_colors_selected(module_index, colors)
            )
            self.master.wait_window(color_picker)
        elif module.type == "1x1":
            color_code = colorchooser.askcolor(title=f"Select color for Module {module_index}")
            if color_code[1]:
                self.on_colors_selected(module_index, [color_code[1]])

    def on_colors_selected(self, module_index, colors):
        """Callback function to handle color selection."""
        self.layout.set_module_colors(module_index, colors)
        self.update_module_display()
        messagebox.showinfo("Success", f"Colors set for module {module_index + 1}")


    def add_image_to_layout(self, start_module):
        """Opens a dialog to select an image and add it to the layout."""
        if self.layout is None:
            messagebox.showwarning("Warning", "Layout not initialized.")
            return

        filepath = filedialog.askopenfilename(
            defaultextension=".png", filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        max_modules = tk.simpledialog.askinteger(
            "Max Modules", "Enter max number of modules for the image to span:"
        )
        if max_modules is None:
            return

        try:
            self.layout.set_image(filepath, start_module, max_modules)
            self.update_module_display()
            messagebox.showinfo("Success", "Image added to layout.")
        except Exception as e:
            messagebox.showerror("Error", f"Error adding image: {e}")


    def update_module_display(self):
        """Updates the module display efficiently by recreating widgets."""
        for widget in self.module_list_frame.winfo_children():
            widget.destroy()

        if self.layout is None:
            return

        for i, module in enumerate(self.layout.get_modules()):
            frame = tk.Frame(self.module_list_frame, bd=1, relief=tk.RAISED)
            frame.pack(fill=tk.X, padx=5, pady=2)

            label_text = f"Module {i + 1}: {module.type}"
            if module.is_used():
                label_text += " (Used by Image)"

            tk.Label(frame, text=label_text).pack(side=tk.LEFT, padx=5)

            if module.type == "5x5_clear":
                tk.Button(frame, text="Set Image", command=lambda idx=i: self.add_image_to_layout(idx)).pack(side=tk.LEFT)
                tk.Button(frame, text="Set Colors", command=lambda idx=i: self.set_module_colors(idx)).pack(side=tk.LEFT)
            else:
                tk.Button(frame, text="Set Color", command=lambda idx=i: self.set_module_colors(idx)).pack(side=tk.LEFT)

            tk.Button(frame, text="Remove", command=lambda idx=i: self.remove_module(idx)).pack(side=tk.RIGHT)


    def send_layout_command(self):
        """Sends the current layout configuration to the Yeelight device."""
        if self.cube is None:
            messagebox.showwarning("Warning", "Not connected to a device.")
            return
        if self.layout is None:
            messagebox.showwarning("Warning", "Layout not defined.")
            return

        try:
            raw_rgb_data = self.layout.get_raw_rgb_data()
            self.cube.draw_matrices(raw_rgb_data)
            messagebox.showinfo("Success", "Layout sent to device!")
        except CubeMatrixException as e:
            messagebox.showerror("Error", f"Error sending command: {e}")


root = tk.Tk()
gui = YeelightGUI(root)
root.mainloop()