# Generated by Django 5.1.4 on 2024-12-17 18:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0027_alter_categories_name_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categories',
            name='name_category',
            field=models.CharField(max_length=30),
        ),
    ]
