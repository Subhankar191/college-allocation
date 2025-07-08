from django.urls import path
from . import views

app_name = 'candidates'

urlpatterns = [
    path('signup/', views.candidate_signup, name='candidate_signup'),
    path('login/', views.candidate_login, name='candidate_login'),
    path('logout/', views.candidate_logout, name='candidate_logout'),
    path('register/', views.candidate_register, name='candidate_register'),
    path('home/', views.candidate_home, name='candidate_home'),

    path('add_preference/<int:college_id>/<int:course_id>/', views.add_preference, name='add_preference'),
    path('remove_preference/<int:college_id>/<int:course_id>/', views.remove_preference, name='remove_preference'),
    path('list/', views.college_course_view, name='college_course_view'),
    path('result/', views.get_candidate_allocation, name='get_candidate_allocation'),
    path('candidate_info/', views.candidate_info, name='candidate_info'),

    path('payment/', views.payment, name='payment'),
    path('process_payment/', views.process_payment, name='process_payment'),
    path('confirm_payment/', views.confirm_payment, name='confirm_payment'),
    path('view_allocation/', views.view_allocation, name='view_allocation'),
    path('payment_page/', views.payment_page, name='payment_page'),
    path('offer_letter/', views.download_offer_letter, name='download_offer_letter'),

]