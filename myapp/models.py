from django.db import models
from datetime import datetime
from django.utils import timezone

# Create your models here.

class Questions(models.Model):
    question = models.CharField(max_length=200)
    created_at = models.DateTimeField()

    def __str__(self):
        return self.question

class Answers(models.Model):
    question = models.ForeignKey(Questions,on_delete=models.CASCADE)
    answer = models.CharField(max_length=100)
    created_at = timezone.now()

    def __str__(self):
        return self.answer
