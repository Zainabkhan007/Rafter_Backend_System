# Generated by Django 5.1.4 on 2024-12-14 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0020_alter_menu_id_alter_menuitems_nutrient_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menu',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]