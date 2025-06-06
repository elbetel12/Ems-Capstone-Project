# Generated by Django 4.2.13 on 2024-09-21 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0022_performance'),
    ]

    operations = [
        migrations.AddField(
            model_name='leave',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='leave_paper/'),
        ),
        migrations.AlterField(
            model_name='leave',
            name='leave_type',
            field=models.CharField(choices=[('Sick', 'Sick'), ('Vacation', 'Vacation'), ('Maternity', 'Maternity'), ('Paternity', 'Paternity'), ('Unpaid', 'Unpaid'), ('Annual', 'Annual'), ('Casual', 'Casual'), ('Education', 'Education')], max_length=20),
        ),
    ]
