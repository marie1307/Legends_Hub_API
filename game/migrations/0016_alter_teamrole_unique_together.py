# Generated by Django 5.0.2 on 2024-03-18 17:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0015_alter_team_member_count_alter_team_status'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='teamrole',
            unique_together={('team', 'member', 'role')},
        ),
    ]