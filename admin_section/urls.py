from django.urls import path,include
from . import views
# from .views import StudentSearchView
urlpatterns = [
   # For registration
    path('password-reset/', views.password_reset, name='password_reset'), 
    path('password/reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),

    path("register/",views.register,name='register'),
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
    path('login/', views.login,name='login'),
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('admin_login/', views.admin_login,name='admin_login'),
    path('get_user_info/<int:id>/<str:user_type>/', views.get_user_info, name='get_user_info'),
    path('update_user_info/<int:id>/<str:user_type>/', views.update_user_info, name='update_user_info'),
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/social/', include('allauth.socialaccount.urls')),
    path('auth/social_callback_register/', views.social_callback_register, name='social_callback_register'),
    path('auth/complete_social_signup/', views.complete_social_signup, name='complete_social_signup'),

    # path('update_profile/<str:user_type>/<int:user_id>/', views.update_profile, name='update_profile'),
     
    path('get_cateenstaff/', views.get_cateenstaff, name='get_cateenstaff'),
    path('cateenstaff_by_id/<int:pk>/', views.cateenstaff_by_id, name='cateenstaff_by_id'),

    path('add_child/', views.add_child, name='add_child'),
    path('edit_child/<int:child_id>/', views.edit_child, name='edit_child'),
    path('all-users/', views.all_users_report, name='all_users_report'),
    

    # Primary School Urls
    path("add_primary_school/",views.add_primary_school,name='add_primary_school'),
    path("primary_school/",views.primary_school,name='primary_school'),
    path("primary_school/<int:pk>/", views.delete_primary_school, name='delete_primary_school'),
    path('primary_school/search', views.PrimarySearch.as_view(), name='PrimarySearch'),

    path('primary_school/<int:school_id>/teacher/', views.add_and_get_teacher, name='add_and_get_teacher'), 
    path('primary_school/<int:school_id>/teacher/<int:teacher_id>/', views.update_delete_teacher, name='update_delete_teacher'),
    path('get_teachers/', views.get_teachers, name='get_teachers'), 
  
    path('primary_school/<int:school_id>/student/', views.get_student_detail, name='get_student_detail'), 
    path('primary_school/<int:school_id>/student/<int:student_id>/', views.update_delete_student, name='update_delete_student'), 
    path('primary_student/search', views.StudentSearch.as_view(), name='StudentSearch'),
     # Secondary School Urls
    path("add_secondary_school/",views.add_secondary_school,name='add_secondary_school'),
    path("secondary_school/",views.secondary_school,name='secondary_school'),
    path("secondary_school/<int:pk>/", views.delete_secondary_school, name='delete_secondary_school'),


    path('add_secondary_student/<int:school_id>/', views.add_secondary_student, name='add_secondary_student'),
    path('secondary_school/<int:school_id>/student/<int:student_id>/', views.update_delete_secondary_student, name='update_delete_secondary_student'),

# Category
    path("get_category/",views.get_category,name='get_category'),
    path("get_allergy/",views.get_allergy,name='get_allergy'),
#    Menu
    path("add_menu/",views.add_menu,name='add_menu'),
    path("create_cycle/",views.create_cycle,name='create_cycle'),
    path("get_cycle_menus/",views.get_cycle_menus,name='get_cycle_menus'),
    path("get_all_cycles_with_menus/",views.get_all_cycles_with_menus,name='get_all_cycles_with_menus'),
    path("get_complete_menu/",views.get_complete_menu,name='get_complete_menu'),
    path("activate_cycle/",views.activate_cycle,name='activate_cycle'),

    path("edit_menu/<int:id>/",views.edit_menu,name='edit_menu'),
    path("get_cycle_names/",views.get_cycle_names,name='get_cycle_names'),
    # path('orders/excel/', views.OrdersExcelDownloadView.as_view(), name='orders_excel_download'),
    
    path("add_menu_item/",views.add_menu_item,name='add_menu_item'),
    path("get_menu_items/",views.get_menu_items,name='get_menu_items'),
    path('update_menu_items/<int:pk>/', views.update_menu_items, name='update_menu_items'),
    path("get_active_menu/",views.get_active_menu,name='get_active_menu'),

    # View Registered Students
    path("view_students/",views.view_students,name='view_students'),
    path("edit_student/<int:student_id>/",views.edit_student,name='edit_student'),


#    Order
    path("create_order/",views.create_order,name='create_order'),
    path("add_order_item/",views.add_order_item,name='add_order_item'),
    path('complete_order/', views.complete_order, name='complete_order'),
    path('cancel_order/', views.cancel_order, name='cancel_order'),
    path('get_all_orders/', views.get_all_orders, name='get_all_orders'),
    path('get_order_by_id/<int:order_id>/', views.get_order_by_id, name='get_order_by_id'),
    path('get_orders_by_user/', views.get_orders_by_user, name='get_orders_by_user'),
    path('get_orders_by_school/', views.get_orders_by_school, name='get_orders_by_school'),

    path('contactmessage/', views.contactmessage, name='contactmessage'),

#  Credits
   path('top_up_credits/', views.top_up_credits, name='top_up_credits'),

   path('payment/', views.CreateOrderAndPaymentAPIView.as_view(), name='create-payment-intent'),
   path('top_up_payment/', views.top_up_payment, name='top_up_payment'),

   path('download_menu_all/',  views.download_menu, name='download_menu_all'),
   path('download-all-schools-menu/', views.download_all_schools_menu, name='download_all_schools_menu'),
   path("get_menu/",views.get_active_status_menu,name='get_active_status_menu'),
   path("get_user_count/",views.get_user_count,name='get_user_count'),
   path("deactivate_menus/",views.deactivate_menus,name='deactivate_menus'),

   

]




