# Generated by Django 5.1.4 on 2024-12-19 09:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0028_alter_categories_name_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='Allergen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allergy', models.JSONField(default=list)),
            ],
        ),
        migrations.AddField(
            model_name='categories',
            name='emoji',
            field=models.ImageField(blank=True, null=True, upload_to='categories_images/'),
        ),
        migrations.AddField(
            model_name='categories',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='categories_images/'),
        ),
        migrations.AlterField(
            model_name='menuitems',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='menuitems', to='admin_section.categories'),
        ),
        migrations.AddField(
            model_name='menuitems',
            name='allergies',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='admin_section.allergen'),
        ),
    ]