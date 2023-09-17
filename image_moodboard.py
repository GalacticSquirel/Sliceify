from typing import Required
from PIL import Image
import os
from random import shuffle , randint
import tqdm
# Set the dimensions of the output grid image
grid_width, grid_height = 1920, 1080

# Set the number of rows and columns in the grid
num_rows, num_cols = 4, 5  # You can adjust these as needed
temp_num_rows = num_rows + 1
temp_num_cols = num_cols + 1
# Create an empty grid image
grid_image = Image.new("RGB", (grid_width, grid_height))

# Get the list of image files in the folder
folder_path = 'cam_anderson'  # Replace with the path to your folder
image_files = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
images_required = temp_num_cols * temp_num_rows
if len(os.listdir('cam_anderson')) < images_required:
    print(f"You need {images_required} images to create a moodboard with {num_rows} rows and {num_cols} columns")
    quit()
shuffle(image_files)
interval = temp_num_cols
sublists = [image_files[i:i + interval] for i in range(0, len(image_files), interval)]

offsets = {}
for i, image_list in enumerate(sublists):
    random_number = randint(-300,-100)
    for x in image_list:
        offsets[x] = random_number
# Iterate over the images and paste them onto the grid

for i, (image_file, offset) in enumerate(offsets.items()):
    if i >= temp_num_rows * temp_num_cols:
        break  # Stop if we've filled the grid

    # Open the image
    img = Image.open(os.path.join(folder_path, image_file))

    # Calculate the position to paste the image
    col = i // temp_num_cols

    row = i % temp_num_cols

    # Calculate the size of each cell in the grid
    cell_width = grid_width // num_cols
    cell_height = grid_height // num_rows

    # Resize the image to fit the cell size
    img = img.resize((cell_width, cell_height), Image.Resampling.LANCZOS)

    # Calculate the paste position
    paste_x = col * cell_width
    paste_y = (row * cell_height) + offset

    # Paste the image onto the grid
    grid_image.paste(img, (paste_x, paste_y))

# Save the final grid image
# rgba_image = grid_image.convert("RGBA")

# # Define a darkness factor (0.5 makes the image half as bright, adjust as needed)
# darkness_factor = 0.5

# # Apply the darkness factor to each pixel's RGB values
# for x in range(rgba_image.width):
#     for y in range(rgba_image.height):
#         r, g, b, a = rgba_image.getpixel((x, y))
#         r = int(r * darkness_factor)
#         g = int(g * darkness_factor)
#         b = int(b * darkness_factor)
#         rgba_image.putpixel((x, y), (r, g, b, a))

grid_image.save('output_grid_image.png')  # Change the filename as needed
