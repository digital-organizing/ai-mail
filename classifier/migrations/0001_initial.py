# Generated by Django 4.2.9 on 2024-01-10 08:41

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Classifier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('uuid', models.UUIDField(default=uuid.uuid4)),
                ('model', models.FileField(upload_to='models/')),
                ('language', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('label', models.CharField()),
                ('classifier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='classifier.classifier')),
            ],
        ),
    ]
