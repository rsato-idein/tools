import os
from PIL import Image

DIR1 = 'human_above_camera'
DIR2 = 'human_front_camera'

for cur_dir, _, file_names in os.walk(DIR1):
    for file_name in file_names:
        if file_name.endswith('.jpg'):
            path1 = os.path.join(cur_dir, file_name)
            path2 = path1.replace(DIR1, DIR2)
            
            img = Image.new('RGB', (128, 256))
            img.paste(Image.open(path1), (0, 0))
            img.paste(Image.open(path2), (0, 128))
            img.save(file_name)
