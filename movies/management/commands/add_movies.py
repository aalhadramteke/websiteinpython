from django.core.management.base import BaseCommand
from movies.models import Movie
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Add sample movies to the database with images'

    def handle(self, *args, **options):
        movies_data = [
            {'title': 'The Matrix', 'price': 250, 'image_filename': 'Matrix.png'},
            {'title': 'Inception', 'price': 250, 'image_filename': 'Inception.png'},
            {'title': 'Interstellar', 'price': 250, 'image_filename': 'Interstellar.png'},
            {'title': 'The Dark Knight', 'price': 250, 'image_filename': 'DarkKnight.png'},
            {'title': 'Oppenheimer', 'price': 250, 'image_filename': 'Oppenheimer.png'},
        ]
        
        media_path = settings.MEDIA_ROOT / 'movie_images'
        
        for data in movies_data:
            movie, created = Movie.objects.get_or_create(
                title=data['title'],
                defaults={'price': data['price']}
            )
            
            image_path = os.path.join('movie_images', data['image_filename'])
            full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)
            
            if os.path.exists(full_image_path) and (not movie.image or not movie.image.name):
                movie.image.name = image_path
                movie.save()
                self.stdout.write(self.style.SUCCESS(f"Assigned image to {movie.title}: {image_path}"))
            elif created:
                self.stdout.write(self.style.SUCCESS(f"Created movie: {movie.title}"))
            else:
                self.stdout.write(f"Movie already exists: {movie.title} (image: {movie.image.name if movie.image else 'None'})")
        
        self.stdout.write(self.style.SUCCESS('All movies and images processed'))

