# Generated by Django 4.2 on 2023-04-19 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_productclass_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='productattribute',
            name='required',
            field=models.BooleanField(default=False),
        ),
    ]
