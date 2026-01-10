from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates a superuser if one does not exist.'

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'gemini-cli-password')
            self.stdout.write(self.style.SUCCESS('Successfully created superuser "admin"'))
        else:
            self.stdout.write(self.style.WARNING('Superuser "admin" already exists.'))
