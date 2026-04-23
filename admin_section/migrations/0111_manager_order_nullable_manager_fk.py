from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0110_manager_generic_remove_school'),
    ]

    operations = [
        migrations.AlterField(
            model_name='managerorder',
            name='manager',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orders',
                to='admin_section.manager',
            ),
        ),
    ]
