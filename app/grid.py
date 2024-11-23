import tkinter as tk
from tkinter import colorchooser

class ColorPickerGrid(tk.Toplevel): # new class for color picker grid.
    def __init__(self, parent, module_index, initial_colors, callback): # takes initial colors and a callback
        super().__init__(parent)
        self.title(f"Color Picker for Module {module_index}")
        self.colors = initial_colors  # store the initial colors
        self.callback = callback
        self.buttons = [] # Keep track of buttons

        for i in range(5): # Create the 5x5 grid of buttons.
            row = []
            for j in range(5):
                button = tk.Button(
                    self,
                    bg=self.colors[i * 5 + j],  # Set initial button color
                    command=lambda row=i, col=j: self.choose_color(row, col),
                    width=2, height=1
                )

                button.grid(row=i, column=j)
                row.append(button)

            self.buttons.append(row)

        tk.Button(self, text="OK", command=self.apply_colors).grid(row=5, columnspan=5)


    def choose_color(self, row, col):
        color_code = colorchooser.askcolor(title="Choose Color")
        if color_code[1]:
            self.colors[row * 5 + col] = color_code[1]
            self.buttons[row][col].config(bg=color_code[1])


    def apply_colors(self): # call the callback
      self.callback(self.colors) # send colors to callback
      self.destroy()