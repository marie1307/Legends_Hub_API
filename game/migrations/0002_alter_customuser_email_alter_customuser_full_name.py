# Generated by Django 5.0.2 on 2024-03-06 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='full_name',
            field=models.CharField(max_length=100, verbose_name='full name'),
        ),
    ]
