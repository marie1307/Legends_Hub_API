# Generated by Django 5.0.2 on 2024-03-15 20:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0009_alter_team_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='invitation',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='invitation',
            name='role',
            field=models.CharField(choices=[('Top lane', 'Top lane'), ('Mid lane', 'Mid lane'), ('Jungle', 'Jungle'), ('Bot lane', 'Bot lane'), ('Support', 'Support'), ('Sub player 1', 'Sub player 1'), ('Sub player 2', 'Sub player 2')], default=1, max_length=20),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='invitation',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_invitations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='invitation',
            unique_together={('sender', 'receiver', 'team', 'role')},
        ),
    ]
