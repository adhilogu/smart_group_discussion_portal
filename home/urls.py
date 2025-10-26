from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [

    path('', views.index,  name='index'),
    path('profile/', views.profile_page,  name='profile_page'),
    path('accounts/register/', views.register, name='register'),


    path('voting-simulator/', views.voting_simulator, name='voting_simulator'),

    #availble slot and and booking
    path('available_slots/', views.available_slots_page,  name='available_slots_page'),

    path('my_slots/', views.my_slots_page,  name='my_slots_page'),
    path('event/<int:event_id>/', views.event_details, name='event_details'),

    #joining page
    path('join/<str:slot_id>/', views.joining_page, name='joining_page'),
    path('join/<str:slot_id>/update-status/', views.update_join_status, name='update_join_status'),
    path('join/<str:slot_id>/check-status/', views.check_join_status, name='check_join_status'),

    # room page
    path('room/<str:slot_id>/', views.room_page, name='room_page'),
    path('slot/<str:slot_id>/room/', views.room_page, name='room_page'),


    path('slot/<str:slot_id>/group-updates/', views.group_updates, name='group_updates'),
    path('slot/<str:slot_id>/results/', views.session_results, name='session_results'),

    # Host Slot page
    path('host-slots/', views.host_slots_page, name='host_slots_page'),
    path('host-slot/<str:slot_id>/', views.host_slot_detail, name='host_slot_detail'),
    path('create-slot/', views.create_slot, name='create_slot'),
    path('api/get_levels_for_event/<int:event_id>/', views.get_levels_for_event, name='get_levels_for_event'),
    path('join-group-from-qr/', views.join_group_from_qr, name='join_group_from_qr'),
    path('host/slot/<str:slot_id>/ended-groups/', views.fetch_ended_groups, name='fetch_ended_groups'),
    path('reports/<str:report_filename>/', views.download_report, name='download_report'),

              ]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
