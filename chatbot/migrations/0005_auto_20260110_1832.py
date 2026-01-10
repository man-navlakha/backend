# Inside the new migration file, e.g., chatbot/migrations/0005_...py

from django.db import migrations

def create_production_superuser(apps, schema_editor):
    """
    Creates a superuser for production.
    """
    # We get the User model this way for migrations.
    User = apps.get_model('auth', 'User')

    username = 'admin' # You can change this
    email = 'admin@`example.com`' # You can change this
    password = 'YourSecurePasswordHere' # <-- CHANGE THIS!

    # Check if the user already exists before creating.
    if not User.objects.filter(username=username).exists():
        print(f'Creating production superuser: {username}')
        User.objects.create_superuser(username=username, email=email, password=password)
    else:
        print(f'Production superuser ({username}) already exists.')


class Migration(migrations.Migration):

    # This should be the name of the migration file before this one.
    # Check your '`chatbot/migrations`' folder to confirm '0004_...' is correct.
    dependencies = [
        ('chatbot', '0004_chatsession_chatmessage'),
    ]

    operations = [
        # This is the line that runs our function.
        migrations.RunPython(create_production_superuser),
    ]

