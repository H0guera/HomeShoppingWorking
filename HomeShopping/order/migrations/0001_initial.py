# Generated by Django 4.2 on 2023-04-06 11:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('product', '0001_initial'),
        ('basket', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(db_index=True, max_length=128, unique=True)),
                ('total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('guest_email', models.EmailField(blank=True, max_length=254)),
                ('date_placed', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('basket', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='basket.basket')),
            ],
        ),
        migrations.CreateModel(
            name='OrderLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='order.order', verbose_name='Order')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.product', verbose_name='Product')),
                ('stockrecord', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.stockrecord', verbose_name='Stock record')),
            ],
        ),
        migrations.CreateModel(
            name='ShippingAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=255)),
                ('last_name', models.CharField(blank=True, max_length=255)),
                ('line1', models.CharField(max_length=255)),
                ('line2', models.CharField(blank=True, max_length=255)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(blank=True, help_text='In case we need to call you about your order', max_length=128, region=None)),
                ('notes', models.TextField(blank=True, help_text='Tell us anything we should know when delivering your order.', verbose_name='Instructions')),
            ],
        ),
        migrations.CreateModel(
            name='OrderLineAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=128)),
                ('value', models.CharField(max_length=128)),
                ('line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='order.orderline')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='order.shippingaddress', verbose_name='Shipping Address'),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to=settings.AUTH_USER_MODEL),
        ),
    ]
