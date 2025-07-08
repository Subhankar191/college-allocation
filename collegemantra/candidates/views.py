# ✅ views.py
from django.db import transaction, connection
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.http import HttpResponse
from .models import Candidate
import time
import random
import logging
from reportlab.pdfgen import canvas
from io import BytesIO

logger = logging.getLogger(__name__)

# --------------------- Utility ---------------------
def is_candidate(user):
    return Candidate.objects.filter(username=user.username).exists()

def candidate_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not is_candidate(request.user):
            messages.error(request, "You must be a candidate to access this page.")
            return redirect("candidates:candidate_register")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# --------------------- Authentication ---------------------
def candidate_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(username=username, password=password)
                    user.save()
                messages.success(request, "Candidate registered successfully!")
                return redirect('candidates:candidate_login')
            except Exception as e:
                messages.error(request, f"Error during signup: {e}")
                return redirect('candidates:candidate_signup')
        else:
            messages.error(request, "Passwords do not match.")

    return render(request, 'candidates/signup.html')

def candidate_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect("candidates:candidate_home")
        messages.error(request, 'Invalid credentials')
    return render(request, 'candidates/login.html')

def candidate_logout(request):
    logout(request)
    return redirect("users:home")

# --------------------- Candidate ---------------------
@login_required(login_url='candidates:candidate_login')
def candidate_register(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                Candidate.objects.create(
                    username=request.user.username,
                    Roll_No=request.POST.get('roll_no'),
                    Candidate_Name=request.POST.get('c_name'),
                    Gender=request.POST.get('gender'),
                    DOB=request.POST.get('dob'),
                    Candidate_Rank=request.POST.get('rank'),
                    XII_Percentage=request.POST.get('xii_percentage'),
                    Category=request.POST.get('category'),
                    Nationality=request.POST.get('nationality'),
                    Address=request.POST.get('address'),
                    Email=request.POST.get('email'),
                    Phone=request.POST.get('phone')
                )
                messages.success(request, "Candidate registered successfully!")
                return redirect('candidates:candidate_home')
        except Exception as e:
            messages.error(request, f"An error occurred during registration: {e}")
            return redirect('candidates:candidate_register')

    return render(request, 'candidates/register.html')

@login_required(login_url='candidates:candidate_login')
def candidate_home(request):
    return render(request, 'candidates/home.html')

@login_required
def candidate_info(request):
    candidate = Candidate.objects.filter(username=request.user.username).first()
    return render(request, 'candidates/candidate_info.html', {'candidate': candidate})

# --------------------- Preferences ---------------------
@login_required(login_url='candidates:candidate_login')
def add_preference(request, college_id, course_id):
    candidate_id = request.user.username
    with transaction.atomic():
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM Preference p
                    JOIN can_pref cp ON cp.Choice_ID = p.Choice_ID
                    WHERE cp.username = %s AND p.College_ID = %s AND p.Course_ID = %s
                """, [candidate_id, college_id, course_id])

                if cursor.fetchone()[0] > 0:
                    messages.info(request, "This preference already exists.")
                    return redirect('candidates:college_course_view')

                cursor.execute("""
                    SELECT MAX(p.Choice_No) FROM can_pref cp
                    JOIN Preference p ON cp.Choice_ID = p.Choice_ID
                    WHERE cp.username = %s
                """, [candidate_id])
                new_choice_no = (cursor.fetchone()[0] or 0) + 1

                cursor.execute("""
                    INSERT INTO Preference (College_ID, Course_ID, Choice_No)
                    VALUES (%s, %s, %s)
                """, [college_id, course_id, new_choice_no])
                choice_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO can_pref (username, Choice_ID) VALUES (%s, %s)
                """, [candidate_id, choice_id])

            messages.success(request, f"Preference added successfully with Choice No: {new_choice_no}")
        except Exception as e:
            messages.error(request, f"Error adding preference: {e}")
            raise
    return redirect('candidates:college_course_view')

@login_required(login_url='candidates:candidate_login')
def remove_preference(request, college_id, course_id):
    candidate_id = request.user.username
    with transaction.atomic():
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE cp, p FROM can_pref cp
                    JOIN Preference p ON cp.Choice_ID = p.Choice_ID
                    WHERE cp.username = %s AND p.College_ID = %s AND p.Course_ID = %s
                """, [candidate_id, college_id, course_id])
            messages.success(request, "Preference removed successfully.")
        except Exception as e:
            messages.error(request, f"Error removing preference: {e}")
            raise
    return redirect('candidates:college_course_view')

@login_required(login_url='users:login')
@candidate_required
def college_course_view(request):
    candidate_id = request.user.username
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.College_Name, co.Branch_Name, c.College_ID, co.Course_ID
            FROM College c
            JOIN College_Course cc ON c.College_ID = cc.College_ID
            JOIN Course co ON cc.Course_ID = co.Course_ID;
        """)
        college_courses = cursor.fetchall()

        cursor.execute("""
            SELECT c.College_ID, c.College_Name, co.Course_ID, co.Branch_Name, p.Choice_No
            FROM College c
            JOIN College_Course cc ON c.College_ID = cc.College_ID
            JOIN Course co ON cc.Course_ID = co.Course_ID
            JOIN Preference p ON p.College_ID = c.College_ID AND p.Course_ID = co.Course_ID
            JOIN can_pref cp ON cp.Choice_ID = p.Choice_ID
            WHERE cp.username = %s ORDER BY p.Choice_No;
        """, [candidate_id])
        preferences = cursor.fetchall()

    return render(request, 'candidates/college_course_list.html', {
        'college_courses': college_courses,
        'preferences': preferences
    })

# --------------------- Allocation ---------------------
@login_required(login_url='users:login')
@candidate_required
def get_candidate_allocation(request):
    context = {'allocation_status': None, 'candidate_name': None, 'allocation': None}
    sql_query = """
    SELECT c.Candidate_Name, c.Roll_No, p.Choice_No, cl.College_Name,
           co.Branch_Name, co.Program_Name
    FROM Can_Alloc ca
    JOIN Allocation a ON ca.Allocation_ID = a.Allocation_ID
    JOIN Preference p ON a.Choice_ID = p.Choice_ID
    JOIN College_Course cc ON p.College_ID = cc.College_ID AND p.Course_ID = cc.Course_ID
    JOIN Course co ON cc.Course_ID = co.Course_ID
    JOIN Candidate c ON ca.username = c.username
    JOIN College cl ON cc.College_ID = cl.College_ID
    WHERE ca.username = %s;
    """
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql_query, [request.user.username])
            result = cursor.fetchall()
            if result:
                candidate_name, roll_no, choice_no, college_name, branch_name, program_name = result[0]
                context.update({
                    'candidate_name': candidate_name,
                    'allocation': {
                        'choice_no': choice_no,
                        'roll_no': roll_no,
                        'college_name': college_name,
                        'branch_name': branch_name,
                        'program_name': program_name,
                    },
                    'allocation_status': 'Your allocation is successful!'
                })
            else:
                context['allocation_status'] = 'No allocation found for the given username.'
        except Exception as e:
            context['allocation_status'] = 'Error retrieving allocation details.'
            messages.error(request, f"Error retrieving allocation: {str(e)}")
    return render(request, 'candidates/result.html', context)

# --------------------- Payment ---------------------
def generate_payment_id():
    return int(time.time()) % 1000000  # Unique 6-digit number

def generate_unique_id():
    return random.randint(1000, 9999)

@login_required(login_url='candidates:candidate_login')
@candidate_required
def payment(request):
    return render(request, 'candidates/payment.html')


@login_required(login_url='candidates:candidate_login')
@candidate_required
def process_payment(request):
    if request.method == "POST":
        username = request.user.username
        amount = request.POST.get("amount", 0)
        transaction_id = generate_unique_id()
        payment_no = generate_payment_id()

        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Get allocation ID
                    cursor.execute("SELECT allocation_id FROM can_alloc WHERE username = %s", [username])
                    allocation = cursor.fetchone()
                    if not allocation:
                        return HttpResponse("Allocation not found")

                    allocation_id = allocation[0]

                    # Prevent duplicate payments
                    cursor.execute("SELECT COUNT(*) FROM candidate_payment WHERE username = %s", [username])
                    if cursor.fetchone()[0] > 0:
                        return HttpResponse("Payment already exists for this user.", status=400)

                    # Record payment
                    cursor.execute("""
                        INSERT INTO Payment (transaction_id, payment_no, pay_date)
                        VALUES (%s, %s, %s)
                    """, [transaction_id, payment_no, now()])

                    # Map candidate to payment
                    cursor.execute("""
                        INSERT INTO candidate_payment (username, payment_no)
                        VALUES (%s, %s)
                    """, [username, payment_no])

                    # Update allocation payment status
                    cursor.execute("""
                        UPDATE Allocation
                        SET payment_status = 1
                        WHERE Allocation_ID = %s
                    """, [allocation_id])

                    # Insert confirmation
                    cursor.execute("""
                        INSERT INTO confirms (payment_no, allocation_id)
                        VALUES (%s, %s)
                    """, [payment_no, allocation_id])

                    return HttpResponse("Payment successful!")

        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}", status=500)

    return HttpResponse("Invalid request method.", status=405)


@login_required
@candidate_required
@login_required
@candidate_required
def payment_page(request):
    with connection.cursor() as cursor:
        # Get allocation details along with candidate information
        cursor.execute("""
            SELECT a.Allocation_ID, c.College_Name, co.Branch_Name,
                   co.Program_Name, p.Choice_No, a.Payment_Status,
                   cand.Candidate_Name, cand.Roll_No
            FROM can_alloc ca
            JOIN Allocation a ON ca.Allocation_ID = a.Allocation_ID
            JOIN Preference p ON a.Choice_ID = p.Choice_ID
            JOIN College_Course cc ON p.College_ID = cc.College_ID AND p.Course_ID = cc.Course_ID
            JOIN Course co ON cc.Course_ID = co.Course_ID
            JOIN College c ON cc.College_ID = c.College_ID
            JOIN Candidate cand ON ca.username = cand.username
            WHERE ca.username = %s
        """, [request.user.username])
        allocation = cursor.fetchone()

    if allocation:
        allocation_data = {
            'allocation_id': allocation[0],
            'college_name': allocation[1],
            'course_name': allocation[2],
            'program_name': allocation[3],
            'choice_no': allocation[4],
            'payment_status': allocation[5],
            'candidate_name': allocation[6],  # Added candidate name
            'roll_no': allocation[7]         # Added roll number
        }
    else:
        allocation_data = None

    return render(request, 'candidates/payment.html', {
        'allocation': allocation_data
    })


@login_required
@candidate_required
def view_allocation(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.Candidate_Name, cl.College_Name, co.Branch_Name,
                   p.Choice_No, a.Payment_Status
            FROM can_alloc ca
            JOIN Allocation a ON ca.Allocation_ID = a.Allocation_ID
            JOIN Preference p ON a.Choice_ID = p.Choice_ID
            JOIN College_Course cc ON p.College_ID = cc.College_ID AND p.Course_ID = cc.Course_ID
            JOIN Course co ON cc.Course_ID = co.Course_ID
            JOIN College cl ON cc.College_ID = cl.College_ID
            JOIN Candidate c ON ca.username = c.username
            WHERE ca.username = %s
        """, [request.user.username])
        allocation = cursor.fetchone()

    return render(request, 'candidates/allocation.html', {
        'has_allocation': allocation is not None,
        'allocation': allocation,
        'payment_pending': allocation and not allocation[4] if allocation else False
    })


@login_required
@candidate_required
def confirm_payment(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                payment_no = generate_payment_id()
                transaction_id = generate_unique_id()

                with connection.cursor() as cursor:
                    # Insert payment
                    cursor.execute("""
                        INSERT INTO Payment (Transaction_ID, Payment_No, Pay_Date)
                        VALUES (%s, %s, %s)
                    """, [transaction_id, payment_no, now()])

                    # Link to candidate
                    cursor.execute("""
                        INSERT INTO candidate_payment (username, Payment_No)
                        VALUES (%s, %s)
                    """, [request.user.username, payment_no])

                    # Update allocation
                    cursor.execute("""
                        UPDATE Allocation
                        JOIN can_alloc ON Allocation.Allocation_ID = can_alloc.Allocation_ID
                        SET Allocation.Payment_Status = 1
                        WHERE can_alloc.username = %s
                    """, [request.user.username])

                    # Insert confirmation
                    cursor.execute("""
                        INSERT INTO confirms (Payment_No, Allocation_ID)
                        SELECT %s, Allocation_ID FROM can_alloc WHERE username = %s
                    """, [payment_no, request.user.username])

                messages.success(request, "Payment confirmed! Your allocation is now finalized.")
                return redirect('candidates:view_allocation')

        except Exception as e:
            messages.error(request, f"Payment failed: {str(e)}")
            return redirect('candidates:payment_page')

    return render(request, 'candidates/payment.html')

#--------------------OL-----------
@login_required
@candidate_required
def download_offer_letter(request):
    username = request.user.username
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.Candidate_Name, c.Roll_No, cl.College_Name, co.Branch_Name, 
                   co.Program_Name, p.Choice_No, a.Payment_Status, cp.payment_no
            FROM can_alloc ca
            JOIN Allocation a ON ca.Allocation_ID = a.Allocation_ID
            JOIN Preference p ON a.Choice_ID = p.Choice_ID
            JOIN College_Course cc ON p.College_ID = cc.College_ID AND p.Course_ID = cc.Course_ID
            JOIN Course co ON cc.Course_ID = co.Course_ID
            JOIN College cl ON cc.College_ID = cl.College_ID
            JOIN Candidate c ON ca.username = c.username
            LEFT JOIN candidate_payment cp ON cp.username = c.username
            WHERE ca.username = %s
        """, [username])
        result = cursor.fetchone()

    if not result or result[6] != 1:
        return HttpResponse("Payment not confirmed. Offer letter unavailable.", status=403)

    name, roll_no, college, branch, program, choice_no, _, payment_no = result

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "College Mantra - Offer Letter")

    p.setFont("Helvetica", 12)
    p.drawString(50, 750, f"Candidate Name: {name}")
    p.drawString(50, 730, f"Roll Number: {roll_no}")
    p.drawString(50, 710, f"Allocated College: {college}")
    p.drawString(50, 690, f"Allocated Course: {branch} ({program})")
    p.drawString(50, 670, f"Choice Number: {choice_no}")
    p.drawString(50, 650, f"Payment ID: {payment_no}")
    p.drawString(50, 630, f"Payment Status: Confirmed")
    p.drawString(50, 610, f"Amount Paid: ₹1")

    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 580, "Thank you for participating in the counseling process.")
    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="offer_letter_{roll_no}.pdf"'
    })
