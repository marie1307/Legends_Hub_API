# Generated by Django 5.0.2 on 2024-03-25 13:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0016_alter_teamrole_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('limit', models.IntegerField(blank=True, null=True)),
                ('teams', models.ManyToManyField(related_name='tournaments', to='game.team')),
            ],
        ),
        migrations.CreateModel(
            name='GameSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField()),
                ('score_team_1', models.IntegerField(default=0)),
                ('score_team_2', models.IntegerField(default=0)),
                ('image_team_1', models.ImageField(blank=True, null=True, upload_to='team_photos/')),
                ('image_team_2', models.ImageField(blank=True, null=True, upload_to='team_photos/')),
                ('vote', models.IntegerField(default=0)),
                ('team_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_schedules_team_1', to='game.team')),
                ('team_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_schedules_team_2', to='game.team')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='game.tournament')),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(default=0)),
                ('win', models.IntegerField(default=0)),
                ('lost', models.IntegerField(default=0)),
                ('total_game', models.IntegerField(default=0)),
                ('registered_time', models.DateTimeField(auto_now_add=True)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='games', to='game.team')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='games', to='game.tournament')),
            ],
        ),
    ]