from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Candidate(models.Model):
   
    username = models.IntegerField(primary_key=True,null=False)
# Username as primary key
    Phone = models.CharField(max_length=15)
    Roll_No = models.CharField(max_length=15, unique=True)
    Candidate_Name = models.CharField(max_length=255)  # Candidate name
    Gender = models.CharField(max_length=15)
    DOB = models.DateField()  # Date of Birth
    Candidate_Rank = models.IntegerField()
    XII_Percentage = models.DecimalField(max_digits=5, decimal_places=2)
    Category = models.CharField(max_length=15)
    Nationality = models.CharField(max_length=15)
    Address = models.CharField(max_length=255)
    Email = models.EmailField()  # Use EmailField for validation

    def __str__(self):
        return str(self.Roll_No)
    class Meta:
        db_table = 'Candidate'