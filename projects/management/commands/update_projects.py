from django.core.management.base import BaseCommand
from projects.utils import update_all_project_stats

class Command(BaseCommand):
    help = 'Updates GitHub stats for all projects'

    def handle(self, *args, **options):
        self.stdout.write('Updating project stats from GitHub...')
        count = update_all_project_stats()
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} projects.'))
