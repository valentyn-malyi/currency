# Generated by Django 2.2.1 on 2019-09-20 18:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0012_first'),
    ]

    operations = [
        migrations.RenameField(
            model_name='first',
            old_name='c',
            new_name='n',
        ),
    ]
