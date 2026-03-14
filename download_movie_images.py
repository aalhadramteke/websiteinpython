import os
import requests
from PIL import Image
from io import BytesIO
from django.conf import settings
from movies.models import Movie
from django.core.files.base import ContentFile

urls = {
    'The Matrix': 'https://i.ibb.co/tT4FcT6d/matrix.webp',
    'Inception': 'https://i.ibb.co/TDk5Cs6Z/inception.jpg',
    'Interstellar': 'https://i.ibb.co/p6Cx9yKs/interstellar.png',
    'The Dark Knight': 'https://i.ibb.co/5x9cYnvM/dark-night.webp',
    'Oppenheimer': 'https://i.ibb.co/VWP54CMm/Oppenheimer.webp',
}

os.makedirs(settings.MEDIA_ROOT + '/movie_images', exist_ok=True)

for title, url in urls.items():
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))
        filename = title.replace(' ', '') + '.' + img.format.lower()
        path = os.path.join(settings.MEDIA_ROOT, 'movie_images', filename)
        img.save(path)
        print(f'Downloaded {filename}')
        
        movie = Movie.objects.get(title=title)
        movie.image.save(filename, ContentFile(resp.content))
        movie.save()
        print(f'Assigned to {title}')
    except Exception as e:
        print(f'Error {title}: {e}')

print('Done! Run python manage.py collectstatic --noinput; python manage.py runserver to test.')

