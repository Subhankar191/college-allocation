from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
# import MySQLdb

from django.http import JsonResponse

# Create your views here.

from django.db import transaction

def base(request):
    return render(request,'users/base.html')

def home(request):
    return render(request,'users/home.html')

def about(request):
    return render(request, 'users/about.html')

def contact(request):
    return render(request,'users/contact.html')

def option(request):
    return render(request,'users/register.html')

def important_dates(request): 
    return render(request, 'users/important_dates.html') 

def announcements(request): 
    return render(request, 'users/announcements.html')

def seat_matrix(request):
    # SQL query to fetch the required data
    query = """
    SELECT 
        c.College_Name,
        co.Branch_Name,
        co.Program_Name,
        sm.General,
        sm.General_PwD,
        sm.OBC_NCL,
        sm.OBC_NCL_PwD,
        sm.SC,
        sm.SC_PwD,
        sm.ST,
        sm.ST_PwD,
        sm.Total_Seats,
        sm.Allocated_Seats
    FROM 
        Seat_Matrix sm
    JOIN 
        College_Course cc ON sm.College_ID = cc.College_ID AND sm.Course_ID = cc.Course_ID
    JOIN 
        College c ON cc.College_ID = c.College_ID
    JOIN 
        Course co ON cc.Course_ID = co.Course_ID;
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    # Create a list of dictionaries to hold the data
    college_courses = []
    for row in rows:
        college_courses.append({
            'college_name': row[0],
            'branch_name': row[1],
            'program_name': row[2],
            'general': row[3],
            'general_pwd': row[4],
            'obc_ncl': row[5],
            'obc_ncl_pwd': row[6],
            'sc': row[7],
            'sc_pwd': row[8],
            'st': row[9],
            'st_pwd': row[10],
            'total_seats': row[11],
            'allocated_seats': row[12],
        })
            # Create a context dictionary to pass data to the template
    context = {
        'college_courses': college_courses,
    }

    # Render the template with the context data
    
    return render(request, 'users/seat_matrix.html', context)