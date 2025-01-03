# Generated by Django 5.1.4 on 2025-01-02 09:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0062_remove_order_items_order_items_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='primary_school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_section.primaryschool'),
        ),
        migrations.AddField(
            model_name='order',
            name='secondary_school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_section.secondaryschool'),
        ),
    ]