import os
from PIL import Image, ImageDraw, ImageFont
import io

def create_placeholder(filename, title, year, genre, color='navy'):
    w, h = 300, 450
    img = Image.new('RGB', (w, h), color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', 24)
    except:
        font = ImageFont.load_default()
    draw.text((20, 200), f'{title}', fill='white', font=font)
    draw.text((20, 250), f'({year})', fill='white', font=font)
    draw.text((20, 300), genre, fill='white', font=font)
    img.save(filename)
    print(f'Created {filename}')

movies = [
    ('<a href="https://ibb.co/tT4FcT6d"><img src="https://i.ibb.co/tT4FcT6d/matrix.webp" alt="matrix" border="0"></a>', 'The Matrix', '1999', 'Sci-Fi', 'navy'),
    ('<a href="https://ibb.co/TDk5Cs6Z"><img src="https://i.ibb.co/TDk5Cs6Z/inception.jpg" alt="inception" border="0"></a>', 'Inception', '2010', 'Sci-Fi', 'teal'),
    ('<a href="https://ibb.co/p6Cx9yKs"><img src="https://i.ibb.co/p6Cx9yKs/interstellar.png" alt="interstellar" border="0"></a>', 'Interstellar', '2014', 'Sci-Fi', 'black'),
    ('<a href="https://ibb.co/5x9cYnvM"><img src="https://i.ibb.co/5x9cYnvM/dark-night.webp" alt="dark-night" border="0"></a>', 'The Dark Knight', '2008', 'Action', 'maroon'),
    ('<a href="https://ibb.co/VWP54CMm"><img src="https://i.ibb.co/VWP54CMm/Oppenheimer.webp" alt="Oppenheimer" border="0"></a>', 'Oppenheimer', '2023', 'Drama', 'purple'),
]

os.makedirs('media_root/movie_images', exist_ok=True)

for path, title, year, genre, color in movies:
    create_placeholder(path, title, year, genre, color)
print('All placeholders created! Replace with real images via /admin/')

