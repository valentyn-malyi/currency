# Generated by Django 2.2.1 on 2019-09-20 19:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0015_first_gain'),
    ]

    operations = [
        migrations.RenameField(
            model_name='first',
            old_name='gain_main',
            new_name='gain_mean',
        ),
    ]