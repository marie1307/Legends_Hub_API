# Generated by Django 5.0.2 on 2024-03-17 21:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0011_team_status'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='team',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='team',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_teams', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='invitation',
            unique_together={('receiver', 'team', 'role')},
        ),
        migrations.CreateModel(
            name='TeamRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('Top lane', 'Top lane'), ('Mid lane', 'Mid lane'), ('Jungle', 'Jungle'), ('Bot lane', 'Bot lane'), ('Support', 'Support'), ('Sub player 1', 'Sub player 1'), ('Sub player 2', 'Sub player 2')], max_length=20)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_roles', to=settings.AUTH_USER_MODEL)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roles', to='game.team')),
            ],
            options={
                'unique_together': {('team', 'member')},
            },
        ),
        migrations.DeleteModel(
            name='TeamMembership',
        ),
        migrations.RemoveField(
            model_name='team',
            name='member_count',
        ),
    ]
