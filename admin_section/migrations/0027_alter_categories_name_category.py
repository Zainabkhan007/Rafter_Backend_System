# Generated by Django 5.1.4 on 2024-12-17 18:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0026_remove_menuitems_nutrient_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categories',
            name='name_category',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]
