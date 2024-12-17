# Generated by Django 5.1.4 on 2024-12-15 19:37

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0021_alter_menu_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(blank=True, null=True)),
                ('staff_id', models.IntegerField(blank=True, null=True)),
                ('user_type', models.CharField(max_length=50)),
                ('child_id', models.IntegerField(blank=True, null=True)),
                ('total_price', models.FloatField()),
                ('week_number', models.IntegerField()),
                ('year', models.IntegerField()),
                ('order_date', models.DateTimeField(default=datetime.datetime.utcnow)),
                ('selected_day', models.CharField(max_length=10)),
                ('is_delivered', models.BooleanField(default=False)),
                ('student', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='admin_section.student')),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('fk_menu_item_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_section.menu')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_section.order')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='items',
            field=models.ManyToManyField(through='admin_section.OrderItem', to='admin_section.menu'),
        ),
    ]