from django.db import models
from django.contrib.auth.models import User


class CycleProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    age = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    usual_cycle_length = models.PositiveIntegerField(
        default=28
    )

    usual_period_duration = models.PositiveIntegerField(
        default=5
    )

    bmi = models.FloatField(
        null=True,
        blank=True
    )

    irregular = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.user.username}'s profile"


class CycleRecord(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cycles"
    )

    period_start = models.DateField()

    period_end = models.DateField(
        null=True,
        blank=True
    )

    cycle_length = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    predicted_cycle_length = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    predicted_next_period = models.DateField(
        null=True,
        blank=True
    )

    predicted_next_period_end = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-period_start"]

    def __str__(self):
        return f"{self.user.username} - {self.period_start}"


class SymptomLog(models.Model):

    FLOW_CHOICES = [
        ("light", "Light"),
        ("medium", "Medium"),
        ("heavy", "Heavy"),
    ]

    MOOD_CHOICES = [
        ("happy", "Happy"),
        ("normal", "Normal"),
        ("sad", "Sad"),
        ("irritable", "Irritable"),
        ("anxious", "Anxious"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="symptoms"
    )

    date = models.DateField()

    cramps = models.PositiveIntegerField(
        default=0
    )

    headache = models.BooleanField(
        default=False
    )

    flow = models.CharField(
        max_length=20,
        choices=FLOW_CHOICES,
        blank=True
    )

    mood = models.CharField(
        max_length=20,
        choices=MOOD_CHOICES,
        blank=True
    )

    stress_level = models.PositiveIntegerField(
        default=1
    )

    sleep_hours = models.FloatField(
        null=True,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class NotificationPreference(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    period_reminder = models.BooleanField(
        default=True
    )

    reminder_days_before = models.PositiveIntegerField(
        default=3
    )

    symptom_reminder = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.user.username} notifications"