# Generated by Django 5.0.2 on 2024-03-15 13:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_alter_invitation_sender'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='team',
            unique_together={('creator', 'name')},
        ),
    ]
