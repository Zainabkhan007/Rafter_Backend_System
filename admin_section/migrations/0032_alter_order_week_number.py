# Generated by Django 5.1.4 on 2024-12-20 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0031_canteenstaff_parentregisteration_staffregisteration_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='week_number',
            field=models.IntegerField(null=True),
        ),
    ]