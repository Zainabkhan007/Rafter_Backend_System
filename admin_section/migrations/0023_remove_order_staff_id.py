# Generated by Django 5.1.4 on 2024-12-15 20:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0022_order_orderitem_order_items'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='staff_id',
        ),
    ]
