# Generated by Django 3.2.18 on 2023-03-06 14:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0003_alter_categories_createddate'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.CharField(max_length=1000)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_comment', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Lot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('description', models.CharField(max_length=1000)),
                ('initial_rate', models.FloatField()),
                ('active', models.BooleanField()),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_lot', to=settings.AUTH_USER_MODEL)),
                ('category_id', models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='category_lot', to='auctions.category')),
            ],
        ),
        migrations.CreateModel(
            name='LotImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_image', to='auctions.image')),
                ('lot_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lot_image', to='auctions.lot')),
            ],
        ),
        migrations.CreateModel(
            name='Rate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.FloatField()),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_rate', to=settings.AUTH_USER_MODEL)),
                ('lot_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lot_rate', to='auctions.lot')),
            ],
        ),
        # migrations.DeleteModel(
        #     name='Categories',
        # ),
        # migrations.AddField(
        #     model_name='comment',
        #     name='lot_id',
        #     field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lot_comment', to='auctions.lot'),
        # ),
    ]
