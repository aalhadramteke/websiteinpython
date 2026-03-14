from django.core.management.base import BaseCommand
from movies.models import Movie

class Command(BaseCommand):
    help = 'Add sample movies to the database'

    def handle(self, *args, **options):
        movies = [
            {'title': 'The Matrix', 'Price': 250},
            {'title': 'Inception', 'Price': 250},
            {'title': 'Interstellar', 'Price': 250},
            {'title': 'The Dark Knight', 'Price': 250},
            {'title': 'Oppenheimer', 'Price': 250},
        ]
        for movie_data in movies:
            movie, created = Movie.objects.get_or_create(
                title=movie_data['title'],
                defaults={'price': movie_data['Price']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created movie: {movie.title}"))
            else:
                self.stdout.write(f"Movie already exists: {movie.title}")

        self.stdout.write(self.style.SUCCESS('All movies have been added'))

