# Generated by Django 5.0.2 on 2024-04-14 18:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0017_tournament_gameschedule_game'),
    ]

    operations = [
        migrations.CreateModel(
            name='TournamentRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tournament_registrations', to='game.team')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrations', to='game.tournament')),
            ],
        ),
    ]