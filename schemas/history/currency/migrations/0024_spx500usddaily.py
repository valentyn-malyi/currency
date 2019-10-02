# Generated by Django 2.2.1 on 2019-09-26 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0023_xauusddaily'),
    ]

    operations = [
        migrations.CreateModel(
            name='Spx500UsdDaily',
            fields=[
                ('t', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('high', models.FloatField()),
                ('low', models.FloatField()),
                ('close', models.FloatField()),
            ],
            options={
                'abstract': False,
            },
        ),
    ]