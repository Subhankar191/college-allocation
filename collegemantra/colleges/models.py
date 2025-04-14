from django.db import models

# Create your models here.
class College(models.Model):
    College_ID = models.AutoField(primary_key=True)
    College_Name = models.CharField(max_length=255)
    College_Type = models.CharField(max_length=20)
    Contact_No = models.CharField(max_length=15)
    Location=models.CharField(max_length=255,null=True)  # Using CharField for formatting
    Email = models.EmailField() 
    Website=models.CharField(max_length=255,null=True) # For validation

    def __str__(self):
        return self.College_Name
    class Meta:
        db_table = 'College'