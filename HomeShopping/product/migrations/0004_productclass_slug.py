# Generated by Django 4.2 on 2023-04-12 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0003_alter_productattribute_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='productclass',
            name='slug',
            field=models.SlugField(default='s', max_length=128, unique=True),
            preserve_default=False,
        ),
    ]
