# Generated by Django 2.2.1 on 2019-09-26 16:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0017_third'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='third',
            name='history',
        ),
    ]
