from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0111_manager_order_nullable_manager_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='managerorder',
            name='custom_school_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
