from django.shortcuts import render
from django.http import HttpResponse
from django.db import transaction, connection
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import College  # Import College model
from django.contrib.auth.models import User
from django.urls import reverse

def is_college(user):
    return College.objects.filter(College_ID=user.username).exists()

# Custom decorator to ensure the user is a College member
def college_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not is_college(request.user):
            messages.error(request, "You must be a college member to access this page.")
            return redirect("colleges:college_login")  # Redirect to college login page
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# College login view
def college_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("colleges:college_home")  # Redirect to college home page after successful login
        else:
            messages.error(request, 'Invalid credentials')
            return render(request, 'colleges/login.html')

    return render(request, 'colleges/login.html')


# College signup view
def college_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:
            try:
                # Start the transaction block
                with transaction.atomic():
                    # Create the User instance
                    user = User.objects.create_user(username=username, password=password)
                    user.save()

                    # If everything goes well, commit the transaction
                    messages.success(request, "College registered successfully!")
                    return redirect('colleges:college_login')  # Redirect to login page after registration
                
            except Exception as e:
                # If an error occurs, the transaction will be rolled back
                messages.error(request, f"An error occurred: {e}")
                return redirect('colleges:college_signup')  # Stay on the signup page

        else:
            messages.error(request, "Passwords do not match.")

    return render(request, 'colleges/signup.html')


# College logout view
def college_logout(request):
    logout(request)
    return redirect("users:home")  # Redirect to the homepage of the users app after logout

# College register view
@login_required(login_url='colleges:college_login')  # Ensures the user is logged in before accessing this page
def college_register(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():  # Start a transaction block to ensure atomicity

                # Retrieve the data from the registration form
                college_id = request.user.username  # Using the username as the college_id
                college_name = request.POST.get('college_name')
                college_type = request.POST.get('college_type')
                contact_no = request.POST.get('contact_no')
                email = request.POST.get('email')
                location = request.POST.get('location')
                website = request.POST.get('website')

                # Validate required fields (you can add more validations here as needed)
                if not college_name or not college_type or not contact_no or not email:
                    raise ValueError("All fields are required!")

                # Create and save the College instance
                college = College(
                    College_ID=college_id,  # Using the logged-in user's username as the college ID
                    College_Name=college_name,
                    College_Type=college_type,
                    Contact_No=contact_no,
                    Email=email,
                    Location=location,
                    Website=website
                )
                college.save()

                # If everything goes well, show a success message
                messages.success(request, "College registered successfully!")
                return redirect('colleges:college_home')  # Redirect to the college home page after successful registration

        except Exception as e:
            # If any error occurs, the transaction will be rolled back
            messages.error(request, f"An error occurred during registration: {e}")
            return redirect('colleges:college_register')  # Redirect back to the registration page on error

    # If the method is GET, render the registration form
    return render(request, 'colleges/register.html')


# Home page for colleges
def is_college(user):
    return College.objects.filter(College_ID=user.username).exists()

# Custom decorator to ensure the user is a College member
def college_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not is_college(request.user):
            messages.error(request, "You must be a college member to access this page.")
            return redirect("colleges:college_login")  # Redirect to college login page
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Home page for colleges
def college_home(request):
    return render(request, 'colleges/home.html')

# College courses view
@login_required(login_url='colleges:college_login')   # Ensures the user is logged in before accessing this page
@college_required
def college_courses(request):
    college_id=request.user.username
    # SQL query to fetch seat matrix for a specific college
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
            Course co ON cc.Course_ID = co.Course_ID
        WHERE 
            c.College_ID = %s;
    """

    # Execute the query and fetch data
    with connection.cursor() as cursor:
        cursor.execute(query, [college_id])
        rows = cursor.fetchall()

    # Create a list of dictionaries to hold the data
    college_courses = [
        {
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
        }
        for row in rows
    ]

    # Render the template with the data
    return render(request, "colleges/college_courses.html", {
        "college_courses": college_courses,
        "college_id": college_id,
    })    

@login_required(login_url='colleges:college_login')
@college_required
def show_college_allocation(request):
    college_id = request.user.username  # Assuming the username is the College_ID

    with connection.cursor() as cursor:
        query = '''
        SELECT 
            c.Candidate_Name, 
            c.Gender, 
            c.DOB, 
            c.Candidate_Rank, 
            c.XII_Percentage, 
            c.Category, 
            c.Nationality, 
            c.Address, 
            c.Email, 
            c.Phone, 
            co.College_Name, 
            co.College_Type, 
            co.Location, 
            cu.Branch_Name, 
            cu.Program_Name, 
            a.Allocation_ID, 
            a.Payment_Status
        FROM col_allo ca
        JOIN College co ON ca.College_ID = co.College_ID
        JOIN Course cu ON ca.Course_ID = cu.Course_ID
        JOIN Allocation a ON ca.Allocation_ID = a.Allocation_ID
        JOIN can_alloc ca2 ON a.Allocation_ID = ca2.Allocation_ID
        JOIN Candidate c ON ca2.username = c.username
        WHERE co.College_ID = %s;
        '''
        cursor.execute(query, [college_id])  # Pass the college_id as parameter to filter
        rows = cursor.fetchall()  # Fetch all rows for the specified college

    context = {'students': rows}  # Pass the student data to the template
    return render(request, 'colleges/college_allocation.html', context)


# views.py
@login_required(login_url='colleges:college_login')
@college_required
def update_seats(request):
    college_id = request.user.username

    # SQL query to fetch seat matrix for a specific college
    query = """
        SELECT 
            sm.College_ID, 
            sm.Course_ID, 
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
            Course co ON cc.Course_ID = co.Course_ID
        WHERE 
            c.College_ID = %s;
    """

    # Fetch seat data
    with connection.cursor() as cursor:
        cursor.execute(query, [college_id])
        rows = cursor.fetchall()

    # Prepare data for rendering
    update_seats = [
        {
            'id': row[0],
            'course_id': row[1],
            'college_name': row[2],
            'branch_name': row[3],
            'program_name': row[4],
            'general': row[5],
            'general_pwd': row[6],
            'obc_ncl': row[7],
            'obc_ncl_pwd': row[8],
            'sc': row[9],
            'sc_pwd': row[10],
            'st': row[11],
            'st_pwd': row[12],
            'total_seats': row[13],
            'allocated_seats': row[14],
        }
        for row in rows
    ]

    # Handle form submission for updating seat matrix
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                for course in update_seats:
                    # Get the updated seat values from the form
                    general = int(request.POST.get(f'general_{course["course_id"]}', 0))
                    general_pwd = int(request.POST.get(f'general_pwd_{course["course_id"]}', 0))
                    obc_ncl = int(request.POST.get(f'obc_ncl_{course["course_id"]}', 0))
                    obc_ncl_pwd = int(request.POST.get(f'obc_ncl_pwd_{course["course_id"]}', 0))
                    sc = int(request.POST.get(f'sc_{course["course_id"]}', 0))
                    sc_pwd = int(request.POST.get(f'sc_pwd_{course["course_id"]}', 0))
                    st = int(request.POST.get(f'st_{course["course_id"]}', 0))
                    st_pwd = int(request.POST.get(f'st_pwd_{course["course_id"]}', 0))
                    total_seats = int(request.POST.get(f'total_{course["course_id"]}', 0))

                    # Update the Seat_Matrix table with the new seat data
                    cursor.execute("""
                        UPDATE Seat_Matrix
                        SET General = %s,
                            General_PwD = %s,
                            OBC_NCL = %s,
                            OBC_Ncl_PwD = %s,
                            SC = %s,
                            SC_PwD = %s,
                            ST = %s,
                            ST_PwD = %s,
                            Total_Seats = %s
                        WHERE College_ID = %s AND Course_ID = %s;
                    """, (general, general_pwd, obc_ncl, obc_ncl_pwd, sc, sc_pwd, st, st_pwd, total_seats, college_id, course['course_id']))

            # Show a success message if the update was successful
            messages.success(request, "Seat matrix updated successfully.")
            return redirect('colleges:update_seats')  # Redirect to the same page after submission

        except Exception as e:
            # If there's an error, show an error message
            messages.error(request, f"An error occurred: {str(e)}")

    # Render the template with the current seat data
    return render(request, "colleges/update_seats.html", {
        "update_seats": update_seats,
        "college_id": college_id,
    })