from django.contrib import admin
from .models import Movie, Payment, PaymentIntent,Seat

# Register your models here.

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'get_image_preview', 'created')
    list_editable = ('price',)
    search_fields = ('title',)
    
    def get_image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="50" height="75" />'
        return 'No Image'
    get_image_preview.short_description = 'Image Preview'
    get_image_preview.allow_tags = True

admin.site.register(Seat)
admin.site.register(Payment)
admin.site.register(PaymentIntent)