import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
import logging
from cube_matrix import CubeMatrix, BulbException
from layout import Layout
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


    def create_widgets(self):
        # IP and Port
        tk.Label(self.master, text="IP Address:").grid(row=0, column=0)
        tk.Entry(self.master, textvariable=self.ip).grid(row=0, column=1)

        tk.Label(self.master, text="Port:").grid(row=1, column=0)
        tk.Entry(self.master, textvariable=self.port).grid(row=1, column=1)

        tk.Button(self.master, text="Connect", command=self.connect_to_bulb).grid(row=2, columnspan=2)

        # Module Layout Frame 
        self.module_frame = tk.Frame(self.master)
        self.module_frame.grid(row=3, columnspan=2, pady=(10, 0))

        self.define_layout_button = tk.Button(self.module_frame, text="Define Layout", command=self.define_layout)
        self.define_layout_button.pack()

        # Orientation
        self.orientation_layout_frame = tk.Frame(self.master)  # Combined frame
        self.orientation_layout_frame.grid(row=4, columnspan=2, pady=(10, 0))

        tk.Label(self.orientation_layout_frame, text="Orientation:").pack(side=tk.LEFT)
        tk.Radiobutton(self.orientation_layout_frame, text="Vertical", variable=self.layout_orientation, value="vertical").pack(side=tk.LEFT)
        tk.Radiobutton(self.orientation_layout_frame, text="Horizontal", variable=self.layout_orientation, value="horizontal").pack(side=tk.LEFT)

        self.layout_start_var = tk.StringVar(value="bottom")  # Variable for layout start
        tk.Label(self.orientation_layout_frame, text="Layout Start:").pack(side=tk.LEFT, padx=10)  # Add label
        layout_start_options = {"vertical": ["top", "bottom"], "horizontal": ["left", "right"]}
        self.layout_start_option_menu = tk.OptionMenu(self.orientation_layout_frame, self.layout_start_var, *layout_start_options["vertical"])
        self.layout_start_option_menu.pack(side=tk.LEFT)  # Add option menu

        self.layout_orientation.trace("w", self.update_layout_start_options) # Update options when orientation changes

        # Image Data
        self.image_frame = tk.Frame(self.master)
        self.image_frame.grid(row=5, columnspan=2, pady=(10, 0))

        self.recreate_layout_button = tk.Button(self.master, text="Recreate Layout", command=self.recreate_layout, state=tk.DISABLED)
        self.recreate_layout_button.grid(row=7, columnspan=2, pady=(10, 0))

        # Send Command
        self.send_command_button = tk.Button(self.master, text="Send Command", command=self.send_layout_command)
        self.send_command_button.grid(row=6, columnspan=2, pady=(10, 0))


    def update_layout_start_options(self, *args):
        """Updates the layout start options based on the selected orientation."""
        layout_start_options = {"vertical": ["top", "bottom"], "horizontal": ["left", "right"]}
        current_orientation = self.layout_orientation.get()
        if current_orientation in layout_start_options:
            self.layout_start_var.set(layout_start_options[current_orientation][0])  # Reset the default.
            menu = self.layout_start_option_menu["menu"]
            menu.delete(0, "end")
            for option in layout_start_options[current_orientation]:
                menu.add_command(label=option, command=lambda value=option: self.layout_start_var.set(value))
        else:
            messagebox.showwarning("Error", "Invalid Layout Orientation")


    def connect_to_bulb(self):
        try:
            self.cube = CubeMatrix(self.ip.get(), self.port.get())
            messagebox.showinfo("Success", "Connected to bulb!")
        except BulbException as e:
            messagebox.showerror("Error", f"Could not connect: {e}")


    def define_layout(self):
        self.layout = Layout(self.layout_orientation.get(), self.layout_start.get())
        try:
            num_modules = tk.simpledialog.askinteger("Layout Size", "Enter the number of modules:")
            if num_modules is None or num_modules <= 0:
                raise ValueError("Invalid number of modules.")

            # Get module types using buttons
            module_type_window = tk.Toplevel(self.master)  # create a new window
            module_type_window.title("Define Module Types")

            module_types = []  # Store the added module types

            def add_module_type(module_type):
                module_types.append(module_type)  # corrected module_types append logic
                module_count_label.config(text=f"Modules defined: {len(module_types)}/{num_modules}")  # update count
                if len(module_types) == num_modules:
                    module_type_window.destroy()  # close if we reached the necessary number of modules.


            module_count_label = tk.Label(module_type_window, text=f"Modules defined: 0/{num_modules}")  # label for module count
            module_count_label.pack()

            tk.Button(module_type_window, text="5x5_clear", command=lambda: add_module_type("5x5_clear")).pack()
            tk.Button(module_type_window, text="5x5_blur", command=lambda: add_module_type("5x5_blur")).pack()
            tk.Button(module_type_window, text="1x1", command=lambda: add_module_type("1x1")).pack()

            self.master.wait_window(module_type_window) # Wait for the module selection window to close

            if len(module_types) != num_modules: # User closed the window prematurely
              return # Do not proceed, allow the user to restart layout definition

            self.layout.add_modules_list(module_types)
            self.layout_defined = True
            messagebox.showinfo("Success", "Layout defined.")

            # Show/Enable relevant widgets after layout definition:
            self.define_layout_button.config(state=tk.DISABLED)

            self.module_frame.grid(row=4, columnspan=2, pady=(10, 0)) # Show module frame now.
            self.orientation_layout_frame.grid(row=5, columnspan=2, pady=(10, 0))
            self.image_frame.grid(row=7, columnspan=2, pady=(10, 0))
            self.send_command_button.grid(row=9, columnspan=2, pady=(10, 0)) # Make sure this button exists and is placed after other widgets.

            self.create_module_widgets()
            self.recreate_layout_button.config(state=tk.NORMAL)

        except ValueError as e:
            messagebox.showerror("Error", str(e))


    def recreate_layout(self):
        """Recreates the layout structure without data."""
        try:
            module_types = [module.type for module in self.layout.get_modules()] # get module types
            self.layout = Layout(self.layout_orientation.get(), self.layout_start.get()) # Reset layout, clearing existing data
            self.layout.add_modules_list(module_types)  # Add modules back to the layout
            self.update_module_display()  # Refresh display
            messagebox.showinfo("Success", "Layout recreated (data cleared).")
        except Exception as e:
            messagebox.showerror("Error", f"Error recreating layout: {e}")


    def create_module_widgets(self):
        """Create module-specific widgets."""
        for i, module in enumerate(self.layout.get_modules()): # Use get_modules()
            frame = tk.Frame(self.module_frame)
            frame.pack()

            var = tk.IntVar(value=1 if module.is_used() else 0) # Checkmark variable
            checkmark = tk.Checkbutton(frame, variable=var, state=tk.DISABLED) # Initially disabled checkmark
            checkmark.pack(side=tk.LEFT)

            if module.type == "5x5_clear": # access module.type
                tk.Button(frame, text="Choose Image", command=lambda index=i: self.add_image_to_layout(index)).pack(side=tk.LEFT)
                tk.Button(frame, text="Set Colors", command=lambda index=i: self.set_module_colors(index)).pack(side=tk.LEFT)
            else:  # Access module.type
                tk.Button(frame, text="Set Color", command=lambda index=i: self.set_module_colors(index)).pack(side=tk.LEFT)


    def add_module(self, module_type):
        """Adds a module to the layout."""
        if not self.layout_defined:
            messagebox.showwarning("Warning", "Define the layout first!")
            return

        try:
            self.layout.add_module(module_type)

            # Create widgets for the added module
            self.create_module_widgets()  # Refresh module widgets
        except ValueError:
            messagebox.showerror("Error", "Layout is already full!")


    def set_module_colors(self, module_index):
        """Sets colors for a module, handling different module types and errors."""
        if not self.layout_defined:
            messagebox.showwarning("Warning", "Define layout first!")
            return

        try:
            modules = self.layout.get_modules()

            if module_index < 0 or module_index >= len(modules):
              raise IndexError("Invalid module index")


            module = self.layout.get_modules()[module_index]
            if module.type.startswith("5x5"):
                initial_colors = module.get_colors()  # Use existing module data.
                color_picker = ColorPickerGrid(self.master, module_index, initial_colors,
                                     lambda colors: self.layout.set_module_colors(module_index, colors)) # pass callback
                self.master.wait_window(color_picker)  # Wait for color picker to close
                messagebox.showinfo("Success", f"Colors set for module {module_index}")  # Simplified
            elif module.type == "1x1":
                color_code = colorchooser.askcolor(title=f"Select color for Module {module_index}")
                if color_code[1] is not None:
                    self.layout.set_module_colors(module_index, [color_code[1]])
                    messagebox.showinfo("Success", f"Color set for module {module_index}")
            else: # This handles layout modules that have a value of None, preventing the gui from crashing in such case
                messagebox.showwarning("Warning", "Cannot set colors for this module type (it might not be initialized yet).")
        except (IndexError, ValueError, AttributeError) as e:  # Handle potential errors from layout or color selection
            messagebox.showerror("Error", f"Error setting colors: {str(e)}")

        self.update_module_display()  # update after setting colors or images.


    def add_image_to_layout(self, start_module):
        if not self.layout_defined:
            messagebox.showwarning("Warning", "Define the layout first!")
            return

        filepath = filedialog.askopenfilename(
            defaultextension=".png", filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        max_modules = tk.simpledialog.askinteger("Max Modules", "Enter the maximum number of modules for the image to span:")
        if max_modules is None:  # Handle cancel
            return

        try:
            self.layout.set_image(filepath, start_module, max_modules) # now passes max_modules to set_image
            messagebox.showinfo("Success", f"Image added to layout.")  # More informative message
        except Exception as e:
            messagebox.showerror("Error", f"Error adding image: {e}")  # Handle and display errors
        
        self.update_module_display()


    def update_module_display(self):
        """Updates the module display efficiently."""
        # Iterate through existing widgets, create new only if needed
        i = 0  # index for iterating over the layout modules

        for widget in self.module_frame.winfo_children():
            if isinstance(widget, tk.Frame):  # Module frames
                try:  # Use a try-except to handle potential layout size mismatches if modules were removed.
                    module = self.layout.get_modules()[i]

                    checkmark = next((w for w in widget.winfo_children() if isinstance(w, tk.Checkbutton)), None)
                    if checkmark is None:
                        checkmark_var = tk.IntVar(value=1 if module.is_used() else 0)
                        checkmark = tk.Checkbutton(widget, variable=checkmark_var, state=tk.DISABLED)
                        checkmark.pack(side=tk.LEFT)
                    if module.is_used():
                        checkmark.select()
                    else:
                        checkmark.deselect()
                    i += 1 # update modules index
                except IndexError: # This handles the case where you've removed modules
                    # Remove extra widgets to match the module list size.
                    widget.destroy() # destroy the widgets if they dont have a corresponding module.


    def send_layout_command(self):
        if not self.layout_defined:
            messagebox.showwarning("Warning", "Define the layout first!")
            return

        try:
            self.layout.layout_start = self.layout_start_var.get()  # set layout start from option menu.
            raw_rgb_data = self.layout.get_raw_rgb_data()
            self.cube.draw_matrices(raw_rgb_data)
            messagebox.showinfo("Success", "Layout command sent!")
        except BulbException as e:
            messagebox.showerror("Error", f"Error sending command: {e}")


root = tk.Tk()
gui = YeelightGUI(root)
root.mainloop()