# Generated by Django 3.2.18 on 2023-03-07 21:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0006_auto_20230307_2126'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Categories',
        ),
        migrations.AlterField(
            model_name='lot',
            name='picture',
            field=models.CharField(default='', max_length=64),
        ),
    ]
