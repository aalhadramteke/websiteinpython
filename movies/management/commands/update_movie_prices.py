from django.core.management.base import BaseCommand
from movies.models import Movie

class Command(BaseCommand):
    help = 'Update all movie prices to 250 rupees'

    def handle(self, *args, **options):
        movies = Movie.objects.all()
        
        if not movies.exists():
            self.stdout.write(self.style.WARNING('No movies found in database'))
            return
        
        updated_count = 0
        for movie in movies:
            movie.price = 250
            movie.save()
            updated_count += 1
            self.stdout.write(f"Updated {movie.title} price to ₹250")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} movie(s) to ₹250'))
