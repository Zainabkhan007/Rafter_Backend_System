# Generated by Django 4.2.9 on 2024-12-12 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0010_menu'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menu',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=5),
        ),
    ]