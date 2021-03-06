# Generated by Django 2.2.1 on 2019-09-26 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0016_auto_20190920_2237'),
    ]

    operations = [
        migrations.CreateModel(
            name='Third',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('t', models.PositiveIntegerField()),
                ('currency_pair', models.TextField()),
                ('history', models.PositiveIntegerField()),
                ('gain_mean', models.FloatField()),
                ('state', models.TextField(null=True)),
                ('direction', models.TextField()),
                ('n', models.PositiveIntegerField()),
                ('oanda', models.PositiveIntegerField(null=True)),
                ('str_datetime', models.TextField()),
                ('c', models.PositiveIntegerField(null=True)),
                ('gain', models.FloatField(null=True)),
            ],
            options={
                'unique_together': {('t', 'currency_pair')},
            },
        ),
    ]
