# Generated by Django 2.2.16 on 2022-08-19 18:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20220819_1748'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, help_text='Выберите картинку', upload_to='posts/', verbose_name='Картинка'),
        ),
    ]