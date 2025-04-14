from django.db import transaction, connection
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Candidate  # Import Candidate model
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.http import HttpResponse
import random
import logging

# Utility function to check if the user is a candidate
def is_candidate(user):
    return Candidate.objects.filter(username=user.username).exists()

# Decorator to restrict access to candidates only
def candidate_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not is_candidate(request.user):
            messages.error(request, "You must be a candidate to access this page.")
            return redirect("candidates:candidate_register")  # Redirect to candidate registration
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Candidate registration view
@login_required(login_url='candidates:candidate_login')  # Redirects to login if user is not authenticated
def candidate_register(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Retrieve data from the form
                roll_no = request.POST.get('roll_no')
                username = request.user.username  # Use the logged-in user's username
                rank = request.POST.get('rank')
                c_name = request.POST.get('c_name')
                gender = request.POST.get('gender')
                dob = request.POST.get('dob')
                c_rank = request.POST.get('rank')  # Category rank
                xii_percentage = request.POST.get('xii_percentage')
                category = request.POST.get('category')
                nationality = request.POST.get('nationality')
                address = request.POST.get('address')
                email = request.POST.get('email')
                phone = request.POST.get('phone')

                # Create and save the Candidate instance
                candidate = Candidate(
                    username=username,
                    Roll_No=roll_no,
                    Candidate_Name=c_name,
                    Gender=gender,
                    DOB=dob,
                    Candidate_Rank=c_rank,
                    XII_Percentage=xii_percentage,
                    Category=category,
                    Nationality=nationality,
                    Address=address,
                    Email=email,
                    Phone=phone
                )
                candidate.save()

                messages.success(request, "Candidate registered successfully!")
                return redirect('candidates:candidate_home')
        except Exception as e:
            messages.error(request, f"An error occurred during registration: {e}")
            return redirect('candidates:candidate_register')

    return render(request, 'candidates/register.html')

# Candidate login view
def candidate_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("candidates:candidate_home")  # Redirect to the candidate home page
        else:
            messages.error(request, 'Invalid credentials')  # Show error message for invalid login
            return render(request, 'candidates/login.html')  # Stay on login page if login fails

    return render(request, 'candidates/login.html')  # Render login page for GET requests

# Candidate signup view
def candidate_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:  # Check if passwords match
            try:
                with transaction.atomic():  # Use atomic transaction to ensure safe database operations
                    user = User.objects.create_user(username=username, password=password)
                    user.save()  # Save the new user in the database

                messages.success(request, "Candidate registered successfully!")  # Success message
                return redirect('candidates:candidate_login')  # Redirect to login page after successful signup
            except Exception as e:
                messages.error(request, f"Error during signup: {e}")  # Handle any exception during signup
                return redirect('candidates:candidate_signup')  # Stay on signup page if error occurs
        else:
            messages.error(request, "Passwords do not match.")  # Error message for mismatched passwords

    return render(request, 'candidates/signup.html')  # Render signup page for GET requests

# Candidate home view
@login_required(login_url='candidates:candidate_login')  # Redirect to login if user is not authenticated
def candidate_home(request):
    return render(request, 'candidates/home.html')  # Render candidate home page

# Logout view
def candidate_logout(request):
    logout(request)  # Log out the user
    return redirect("users:home")  # Redirect to the home page of another app (e.g., users app)

# Add preference view
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, connection
from django.shortcuts import redirect
import logging

# Set up logger for better error tracking in production
logger = logging.getLogger(__name__)

# Add preference view
@login_required(login_url='candidates:candidate_login')
def add_preference(request, college_id, course_id):
    candidate_id = request.user.username

    with transaction.atomic():  # Ensure atomic transaction for all DB operations
        try:
            with connection.cursor() as cursor:
                # Check if the preference already exists
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM Preference p
                    JOIN can_pref cp ON cp.Choice_ID = p.Choice_ID
                    WHERE cp.username = %s AND p.College_ID = %s AND p.Course_ID = %s
                """, [candidate_id, college_id, course_id])

                if cursor.fetchone()[0] > 0:
                    messages.info(request, "This preference already exists.")
                    return redirect('candidates:college_course_view')

                # Find the highest Choice_No for the current candidate
                cursor.execute("""
                    SELECT MAX(p.Choice_No)
                    FROM can_pref cp
                    JOIN Preference p ON cp.Choice_ID = p.Choice_ID
                    WHERE cp.username = %s
                """, [candidate_id])
                new_choice_no = (cursor.fetchone()[0] or 0) + 1  # Increment Choice_No

                # Insert the new preference into the Preference table
                cursor.execute("""
                    INSERT INTO Preference (College_ID, Course_ID, Choice_No)
                    VALUES (%s, %s, %s)
                """, [college_id, course_id, new_choice_no])
                choice_id = cursor.lastrowid  # Get the last inserted row's ID

                # Insert into the can_pref table
                cursor.execute("""
                    INSERT INTO can_pref (username, Choice_ID)
                    VALUES (%s, %s)
                """, [candidate_id, choice_id])

            # If the operation is successful, display success message
            messages.success(request, f"Preference added successfully with Choice No: {new_choice_no}")
            logger.info(f"Candidate {candidate_id} added preference with Choice No {new_choice_no}.")

        except Exception as e:
            # In case of error, log it and display an error message
            logger.error(f"Error adding preference for candidate {candidate_id}: {str(e)}")
            messages.error(request, f"Error adding preference: {e}")
            raise  # Re-raise exception to trigger rollback

    return redirect('candidates:college_course_view')

# Remove preference view
@login_required(login_url='candidates:candidate_login')
def remove_preference(request, college_id, course_id):
    candidate_id = request.user.username

    with transaction.atomic():  # Ensure atomic transaction for all DB operations
        try:
            with connection.cursor() as cursor:
                # Delete the preference from both can_pref and Preference tables
                cursor.execute("""
                    DELETE cp, p
                    FROM can_pref cp
                    JOIN Preference p ON cp.Choice_ID = p.Choice_ID
                    WHERE cp.username = %s AND p.College_ID = %s AND p.Course_ID = %s
                """, [candidate_id, college_id, course_id])

            # If the operation is successful, display success message
            messages.success(request, "Preference removed successfully.")
            logger.info(f"Candidate {candidate_id} removed preference for College {college_id} and Course {course_id}.")

        except Exception as e:
            # In case of error, log it and display an error message
            logger.error(f"Error removing preference for candidate {candidate_id}: {str(e)}")
            messages.error(request, f"Error removing preference: {e}")
            raise  # Re-raise exception to trigger rollback

    return redirect('candidates:college_course_view')


# View for college courses list
@login_required(login_url='users:login')  # Assuming the user login is handled by the 'users' app
@candidate_required
def college_course_view(request):
    candidate_id = request.user.username  # Assuming the User model's username is username

    query_courses = """
        SELECT c.College_Name AS college_name, co.Branch_Name AS course_name, 
               c.College_ID AS college_id, co.Course_ID AS course_id
        FROM College c
        JOIN College_Course cc ON c.College_ID = cc.College_ID
        JOIN Course co ON cc.Course_ID = co.Course_ID;
    """

    query_preferences = """
        SELECT c.College_ID, c.College_Name, co.Course_ID, co.Branch_Name AS course_name, p.Choice_No
        FROM College c
        JOIN College_Course cc ON c.College_ID = cc.College_ID
        JOIN Course co ON cc.Course_ID = co.Course_ID
        JOIN Preference p ON p.College_ID = c.College_ID AND p.Course_ID = co.Course_ID
        JOIN can_pref cp ON cp.Choice_ID = p.Choice_ID
        WHERE cp.username = %s
        ORDER BY p.Choice_No;
    """

    with connection.cursor() as cursor:
        cursor.execute(query_courses)
        college_courses = cursor.fetchall()

        cursor.execute(query_preferences, [candidate_id])
        preferences = cursor.fetchall()

    return render(request, 'candidates/college_course_list.html', {
        'college_courses': college_courses,
        'preferences': preferences
    })

@login_required(login_url='users:login')  # Assuming the user login is handled by the 'users' app
@candidate_required
def get_candidate_allocation(request):
    context = {
        'allocation_status': None,
        'candidate_name': None,
        'allocation': None,
    }

    sql_query = """
    SELECT 
        c.Candidate_Name,
        c.Roll_No,
        p.Choice_No,
        cl.College_Name,
        co.Branch_Name,
        co.Program_Name
    FROM 
        Can_Alloc ca
    JOIN 
        Allocation a ON ca.Allocation_ID = a.Allocation_ID
    JOIN 
        Preference p ON a.Allocation_ID = p.Choice_ID
    JOIN 
        College_Course cc ON p.College_ID = cc.College_ID AND p.Course_ID = cc.Course_ID
    JOIN 
        Course co ON cc.Course_ID = co.Course_ID
    JOIN 
        Candidate c ON ca.username = c.username
    JOIN 
        College cl ON cc.College_ID = cl.College_ID
    WHERE 
        ca.username = %s;
    """

    with connection.cursor() as cursor:
        try:
            cursor.execute(sql_query, [request.user.username])  # Pass the logged-in user's username
            result = cursor.fetchall()  # Fetch all results

            if result:
                candidate_name, roll_no, choice_no, college_name, branch_name, program_name = result[0]
                context['candidate_name'] = candidate_name
                context['allocation'] = {
                    'choice_no': choice_no,
                    'roll_no': roll_no,
                    'college_name': college_name,
                    'branch_name': branch_name,
                    'program_name': program_name,
                }
                context['allocation_status'] = 'Your allocation is successful!'
            else:
                context['allocation_status'] = 'No allocation found for the given username.'
        except Exception as e:
            context['allocation_status'] = 'Error retrieving allocation details.'
            messages.error(request, f"Error retrieving allocation: {str(e)}")
            # You could also log the error here if you want

    return render(request, 'candidates/result.html', context)

@login_required(login_url='users:login')  # Assuming the user login is handled by the 'users' app
def candidate_info(request):
    # Fetch candidate data based on the logged-in user's username
    candidate = Candidate.objects.filter(username=request.user.username).first()  # 'first()' to get only one result
    return render(request, 'candidates/candidate_info.html', {'candidate': candidate})

# Payment ID generation functions
def generate_payment_id():
    """Generate a unique random ID."""
    return random.randint(100, 999)

def generate_unique_id():
    """Generate a unique random ID."""
    return random.randint(1000, 9999)

@candidate_required
@login_required(login_url='candidates:candidate_login')
def process_payment(request):
    if request.method == "POST":
        username = request.user.username  # Assuming the user is authenticated
        amount = request.POST.get("amount", 0)
        
        # Generate unique IDs
        transaction_id = generate_unique_id()
        payment_no = generate_payment_id()

        try:
            with transaction.atomic():  # Start the transaction block
                # Define the cursor to interact with the database
                with connection.cursor() as cursor:
                    # Fetch allocation_id for the user
                    cursor.execute(
                        "SELECT allocation_id FROM can_alloc WHERE username = %s",
                        [username],
                    )
                    allocation = cursor.fetchone()
                    if allocation:
                        allocation_id = allocation[0]
                    else:
                        return HttpResponse("Allocation not found")

                    # Check if the user already has an entry in the candidate_payment table
                    cursor.execute(
                        "SELECT COUNT(*) FROM candidate_payment WHERE username = %s",
                        [username],
                    )
                    result = cursor.fetchone()
                    if result[0] > 0:
                        return HttpResponse("Payment already exists for this user.", status=400)

                    # Insert a new payment record
                    cursor.execute(
                        "INSERT INTO payment (transaction_id, payment_no, pay_date) VALUES (%s, %s, %s)",
                        [transaction_id, payment_no, now()],
                    )

                    # Insert into candidate_payment table
                    cursor.execute(
                        "INSERT INTO candidate_payment (username, payment_no) VALUES (%s, %s)",
                        [username, payment_no],
                    )

                    # Update allocation with payment status
                    cursor.execute(
                        "INSERT INTO allocation (allocation_id, payment_status) VALUES (%s, %s)",
                        [allocation_id, "1"],
                    )

                    # Mark the allocation as confirmed
                    cursor.execute(
                        "INSERT INTO confirms (payment_no, allocation_id) VALUES (%s, %s)",
                        [payment_no, allocation_id],
                    )

                    return HttpResponse("Payment successful!")
        except Exception as e:
            # In case of an error, the transaction will be rolled back and the error message will be returned
            return HttpResponse(f"An error occurred: {str(e)}", status=500)

    else:
        return HttpResponse("Invalid request method.", status=405)

@login_required(login_url='candidates:candidate_login')
@candidate_required
def payment(request):
    return render(request, 'candidates/payment.html')
