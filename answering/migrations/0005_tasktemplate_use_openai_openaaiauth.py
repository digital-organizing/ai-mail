# Generated by Django 4.2.9 on 2024-01-10 09:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('answering', '0004_tasktemplate_default_answer'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasktemplate',
            name='use_openai',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='OpenaAIAuth',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_key', models.CharField(max_length=500)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.group')),
            ],
        ),
    ]