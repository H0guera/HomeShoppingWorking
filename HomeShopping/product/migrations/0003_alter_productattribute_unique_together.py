# Generated by Django 4.2 on 2023-04-11 17:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_productattribute_code'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='productattribute',
            unique_together={('code', 'product_class')},
        ),
    ]
