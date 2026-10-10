import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Create an initial Super Admin from environment variables; never reset existing credentials.'
    def handle(self, *args, **options):
        username = os.environ.get('INITIAL_ADMIN_USERNAME')
        password = os.environ.get('INITIAL_ADMIN_PASSWORD')
        if not username and not password:
            return
        if not username or not password:
            raise CommandError('Provide both INITIAL_ADMIN_USERNAME and INITIAL_ADMIN_PASSWORD.')
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write('Initial administrator already exists; unchanged.')
            return
        User.objects.create_superuser(username=username, password=password,
                                      email=os.environ.get('INITIAL_ADMIN_EMAIL', ''))
        self.stdout.write(self.style.SUCCESS('Initial Super Admin created.'))
