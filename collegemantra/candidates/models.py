# ✅ models.py
from django.db import models

class Candidate(models.Model):
    username = models.CharField(max_length=150, primary_key=True)
    Phone = models.CharField(max_length=15)
    Roll_No = models.CharField(max_length=15, unique=True)
    Candidate_Name = models.CharField(max_length=255)
    Gender = models.CharField(max_length=15)
    DOB = models.DateField()
    Candidate_Rank = models.IntegerField()
    XII_Percentage = models.DecimalField(max_digits=5, decimal_places=2)
    Category = models.CharField(max_length=15)
    Nationality = models.CharField(max_length=15)
    Address = models.CharField(max_length=255)
    Email = models.EmailField()

    def __str__(self):
        return str(self.Roll_No)

    class Meta:
        db_table = 'Candidate'
