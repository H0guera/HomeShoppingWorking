# Generated by Django 4.2 on 2023-04-28 12:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_stockrecord_partner_sku'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='productattributevalue',
            unique_together={('attribute', 'product')},
        ),
    ]
