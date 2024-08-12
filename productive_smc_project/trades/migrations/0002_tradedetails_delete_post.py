# Generated by Django 5.0.7 on 2024-07-29 17:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trades", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TradeDetails",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("trade_datetime", models.DateTimeField()),
                ("trade_symbol", models.CharField(max_length=10)),
                (
                    "trade_type",
                    models.CharField(
                        choices=[("Buy", "Buy"), ("Sell", "Sell")], max_length=4
                    ),
                ),
                ("entry_price", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "exit_price",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("quantity", models.IntegerField()),
                ("trade_rationale", models.TextField(blank=True, null=True)),
                ("outcome_analysis", models.TextField(blank=True, null=True)),
                ("emotional_state", models.TextField(blank=True, null=True)),
                ("lessons_learned", models.TextField(blank=True, null=True)),
                ("notes", models.TextField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-trade_datetime"],
            },
        ),
        migrations.DeleteModel(
            name="Post",
        ),
    ]
