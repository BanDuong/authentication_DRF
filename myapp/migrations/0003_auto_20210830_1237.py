# Generated by Django 3.2.4 on 2021-08-30 05:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_makeaudiocaptcha_makeimagecaptcha'),
    ]

    operations = [
        migrations.AlterField(
            model_name='makeaudiocaptcha',
            name='audio_captcha',
            field=models.FileField(blank=True, null=True, upload_to='au_captcha', verbose_name='audio_captcha'),
        ),
        migrations.AlterField(
            model_name='makeimagecaptcha',
            name='image_captcha',
            field=models.ImageField(blank=True, null=True, upload_to='img_captcha', verbose_name='image_captcha'),
        ),
    ]
