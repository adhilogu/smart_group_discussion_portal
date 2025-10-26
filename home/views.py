import copy
import json
from ast import parse
from datetime import timedelta, datetime, timezone
from decimal import Decimal
import random
from django.contrib import messages
from django.db.models import Prefetch
from django.http import JsonResponse, FileResponse, HttpResponse
from django.shortcuts import render, redirect
from admin_datta.forms import RegistrationForm, LoginForm, UserPasswordChangeForm, UserPasswordResetForm, UserSetPasswordForm
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetConfirmView, PasswordResetView
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView
from django.contrib.auth import logout
from datetime import date, timedelta
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from rest_framework.generics import get_object_or_404
from collections import defaultdict
from django.db.models import Count
from collections import defaultdict
import json
from .models import *
from django.shortcuts import render, redirect

from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetConfirmView, PasswordResetView
from django.views.generic import CreateView
from django.contrib.auth import logout
from .models import UserProfile
from .forms import RegistrationForm



import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import os
from django.conf import settings

import logging

logger = logging.getLogger(__name__)
from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_superuser)
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)

        # Check if profile photo is provided
        if 'photo' not in request.FILES:
            form.add_error('photo', 'Profile photo is required')
            context = {'form': form, 'segment': 'register'}
            return render(request, 'accounts/register.html', context)

        if form.is_valid():
            user = form.save()
            profile = UserProfile(
                user=user,
                name=form.cleaned_data.get('name'),
                roll_number=form.cleaned_data.get('roll_number') if form.cleaned_data.get(
                    'user_type') == 'STUDENT' else None,
                user_type=form.cleaned_data.get('user_type'),
                staff_id=form.cleaned_data.get('staff_id') if form.cleaned_data.get('user_type') == 'FACULTY' else None,
                department=form.cleaned_data.get('department'),
                gender=form.cleaned_data.get('gender'),
                batch=form.cleaned_data.get('batch') if form.cleaned_data.get('user_type') == 'STUDENT' else None,
                phone_number=form.cleaned_data.get('phone_number'),
                mail_id=form.cleaned_data.get('email'),
                photo=request.FILES['photo'],
                status='active'
            )
            profile.save()

            # Auto-login the user after registration
            from django.contrib.auth import login
            login(request, user)

            # Redirect to index page instead of login page, but only for regular users
            return redirect('index')
        else:
            print("Register failed!")
    else:
        # Check if user is already logged in
        if request.user.is_authenticated:
            if request.user.is_superuser:
                # Allow superusers to stay on the registration page
                form = RegistrationForm()
            else:
                # Redirect regular users to index if already logged in
                return redirect('index')
        else:
            form = RegistrationForm()

    context = {'form': form, 'segment': 'register'}
    return render(request, 'accounts/register.html', context)



@login_required
def index(request):
    return redirect('available_slots_page')

@login_required
def voting_simulator(request):
    context = {
        'active_page': 'voting_simulator',
    }
    return render(request, 'pages/voting_simulator.html', context)

@login_required
def profile_page(request):
    """View for displaying the user's profile, achievements, and recent activities."""
    # Get the user's profile
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
        print(f"No UserProfile found for user: {request.user.username}")

    # Get user's achievements
    achievements = Achievements.objects.filter(user=request.user).order_by('-created_at')

    # Create a set of achievement identifiers for quick lookups
    achievement_identifiers = {
        (a.slot_id, a.group_name): True
        for a in achievements
    }

    # Get user's slot participations (activities)
    slot_participations = SlotParticipant.objects.filter(
        user=user_profile
    ).select_related(
        'slot',
        'topic'
    ).order_by('-created_at')[:10]  # Limit to 10 most recent activities

    # Fetch all relevant slot groups in a single query to avoid N+1 problem
    slot_ids = [p.slot.id for p in slot_participations]
    group_names = [p.group_name for p in slot_participations]

    # Get all relevant SlotGroups in one query
    slot_groups = {}
    if slot_ids and group_names:
        groups_query = SlotGroup.objects.filter(
            slot__id__in=slot_ids,
            group_name__in=group_names
        ).select_related('event', 'level')

        # Create dictionary for easy lookup
        for group in groups_query:
            key = (group.slot_id, group.group_name)
            slot_groups[key] = group

    # Enhance slot participations with event and level information
    for participation in slot_participations:
        # Add has_achievement flag
        participation.has_achievement = (
                                            participation.slot.slot_id,
                                            participation.group_name
                                        ) in achievement_identifiers

        # Try to get event and level info from corresponding SlotGroup
        key = (participation.slot.id, participation.group_name)
        if key in slot_groups:
            group = slot_groups[key]

            # Store event name directly
            if group.event:
                participation.event_name = group.event.event_name
            else:
                participation.event_name = None

            # Store level name directly from the name field
            if group.level:
                participation.level_name = group.level.name  # Use the actual name field
            else:
                participation.level_name = None
        else:
            participation.event_name = None
            participation.level_name = None

    # Prepare data for charts and analysis
    context = {
        'user_profile': user_profile,
        'achievements': achievements,
        'slot_participations': slot_participations,
        # Add debug data
        'debug_info': {
            'user_type': user_profile.user_type if user_profile else None,
            'roll_number': user_profile.roll_number if user_profile else None,
            'staff_id': user_profile.staff_id if user_profile else None,
        } if user_profile else {}
    }

    if achievements.exists():
        # Event participation analysis
        event_data = achievements.values('event__event_name').annotate(count=Count('event'))
        event_names = json.dumps([event['event__event_name'] for event in event_data])
        event_counts = json.dumps([event['count'] for event in event_data])

        # Level progression analysis
        level_counts = [0, 0, 0, 0]  # Initialize counts for levels 1, 2, 3, 4+
        for achievement in achievements:
            level = achievement.level
            if 1 <= level <= 3:
                level_counts[level - 1] += 1
            else:
                level_counts[3] += 1  # Level 4+

        # Skills analysis (based on achievements)
        technical_skills = {}
        soft_skills = {}

        # Skills mapping dictionary - customize based on your events
        skill_mapping = {
            # Example mappings from events to skills
            'Hackathon': {'Technical': ['Programming', 'Problem Solving'], 'Soft': ['Teamwork']},
            'Workshop': {'Technical': ['Software Development'], 'Soft': ['Learning']},
            'Conference': {'Technical': [], 'Soft': ['Networking', 'Communication']},
            'Competition': {'Technical': ['Technical Knowledge'], 'Soft': ['Time Management']},
            # Add more mappings as needed
        }

        # Count skills from achievements
        skill_counter = defaultdict(int)
        for achievement in achievements:
            event_name = achievement.event.event_name
            if event_name in skill_mapping:
                for skill_type, skills in skill_mapping[event_name].items():
                    for skill in skills:
                        skill_counter[skill] += 1

        # Calculate skill percentages (based on frequency)
        max_skill_count = max(skill_counter.values()) if skill_counter else 1

        for skill, count in skill_counter.items():
            # Determine if it's a technical or soft skill
            skill_level = int((count / max_skill_count) * 100)

            # Determine if technical or soft skill
            is_technical = any(
                skill in skills['Technical']
                for event_mapping in skill_mapping.values()
                for skills in [event_mapping]
            )

            if is_technical:
                technical_skills[skill] = skill_level
            else:
                soft_skills[skill] = skill_level

        # Add chart data to context
        context.update({
            'event_names': event_names,
            'event_counts': event_counts,
            'level_counts': level_counts,
            'technical_skills': technical_skills,
            'soft_skills': soft_skills,
        })

    return render(request, "pages/profile_page.html", context)

@login_required
def available_slots_page(request):
    # Get all active events
    all_active_events = Event.objects.filter(status='active').prefetch_related('levels')

    # Get user's group IDs for efficient comparison
    user_group_ids = request.user.groups.values_list('id', flat=True)
    user_achievements = Achievements.objects.filter(user=request.user)

    # Filter events based on group eligibility
    eligible_events = []
    for event in all_active_events:
        # Check if event has group restrictions
        if event.eligible_groups.exists():
            # Get event's eligible group IDs
            event_eligible_group_ids = event.eligible_groups.values_list('id', flat=True)

            # Check if user belongs to any eligible group
            user_in_eligible_group = False
            for group_id in user_group_ids:
                if group_id in event_eligible_group_ids:
                    user_in_eligible_group = True
                    break

            # Skip this event if user not in any eligible group
            if not user_in_eligible_group:
                continue

        # If we get here, the user is eligible for this event
        eligible_events.append(event)

    events_data = []
    for event in eligible_events:
        # Get eligible levels for this event - levels that are active AND user is in eligible group
        eligible_event_levels = []
        for level in event.levels.filter(status='active').order_by('level'):
            # Check if level has group restrictions
            if level.eligible_groups.exists():
                # Get level's eligible group IDs
                level_eligible_group_ids = level.eligible_groups.values_list('id', flat=True)

                # Check if user belongs to any eligible group
                user_in_eligible_level_group = False
                for group_id in user_group_ids:
                    if group_id in level_eligible_group_ids:
                        user_in_eligible_level_group = True
                        break

                # Skip this level if user not in any eligible group
                if not user_in_eligible_level_group:
                    continue

            # If we get here, the user is eligible for this level
            eligible_event_levels.append(level)

        # Continue with achievement-based eligibility
        user_highest_level = user_achievements.filter(event=event).order_by('-level').first()
        eligible_level = None
        is_participant = False

        if not user_highest_level and eligible_event_levels:
            eligible_level = eligible_event_levels[0]  # First eligible level
        elif user_highest_level and eligible_event_levels:
            # Find the next level after user's highest completed level
            next_level_found = False
            for level in eligible_event_levels:
                if level.level == user_highest_level.level + 1:
                    eligible_level = level
                    next_level_found = True
                    break

            if not next_level_found:
                eligible_level = None

        # Check if user is already a participant in any SlotGroup for this event/level
        if eligible_level:
            # Find active slots for this event/level
            active_slots = Slot.objects.filter(slot_status='live')

            # Look for SlotGroups with this event and level and start_status 'pause'
            slot_groups = SlotGroup.objects.filter(
                slot__in=active_slots,
                event=event,
                level=eligible_level,
                finished=False,
                start_status='pause'  # Only include groups with start_status='pause'
            )

            # Check if user is already a participant in any of these groups
            for group in slot_groups:
                if request.user.userprofile in group.participants.all():
                    is_participant = True
                    break

        available_slot_groups = 0
        if eligible_level and not is_participant:
            # Count available SlotGroups for this event/level in live slots with start_status='pause'
            available_slot_groups = SlotGroup.objects.filter(
                slot__slot_status='live',
                event=event,
                level=eligible_level,

                finished=False,
                start_status='pause'  # Only count groups with start_status='pause'
            ).count()

        events_data.append({
            'event': event,
            'eligible_level': eligible_level,
            'available_slot_groups': available_slot_groups,
            'completed_level': user_highest_level.level if user_highest_level else None,
            'is_participant': is_participant
        })

    context = {
        'events_data': events_data
    }
    return render(request, "pages/available_slots_page.html", context)


@login_required
def event_details(request, event_id):
    # AJAX toggle request handling
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        material_id = request.POST.get('material_id')
        if material_id:
            try:
                # Get the material
                material = Materials.objects.get(id=material_id)

                # Debugging: Print current completed users
                print(f"Current completed users: {list(material.completed_users.all())}")

                # Toggle completion status
                if request.user in material.completed_users.all():
                    material.completed_users.remove(request.user)
                    is_completed = False
                    print(f"Removing user {request.user} from completed users")
                else:
                    material.completed_users.add(request.user)
                    is_completed = True
                    print(f"Adding user {request.user} to completed users")

                # Verify the addition/removal
                print(f"Updated completed users: {list(material.completed_users.all())}")

                # Get all materials for this event and level
                level_materials = Materials.objects.filter(
                    event=material.event,
                    level=material.level,
                    status='active'
                )

                # Calculate completion count
                completed_count = level_materials.filter(
                    completed_users=request.user
                ).count()

                total_count = level_materials.count()
                progress = int((completed_count / total_count) * 100) if total_count > 0 else 0

                return JsonResponse({
                    'status': 'success',
                    'is_completed': is_completed,
                    'progress': progress,
                    'completed_count': completed_count,
                    'total_count': total_count
                })

            except Materials.DoesNotExist:
                print(f"Material with ID {material_id} not found")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Material not found'
                }, status=404)
            except Exception as e:
                print(f"Error toggling material completion: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)

        return JsonResponse({
            'status': 'error',
            'message': 'Material ID is required'
        }, status=400)

    # Rest of the existing view logic
    event = get_object_or_404(Event.objects.prefetch_related('levels'), id=event_id)

    user_achievement = Achievements.objects.filter(
        user=request.user,
        event=event
    ).order_by('-level').first()

    # Get all active levels for this event
    all_event_levels = event.levels.filter(status='active').order_by('level')

    # Get user's groups IDs for more efficient comparison
    user_group_ids = request.user.groups.values_list('id', flat=True)

    # Determine current eligible level for materials
    current_eligible_level = None
    if user_achievement:
        # The level the user is eligible for next
        for level in all_event_levels:
            if level.level == user_achievement.level + 1:
                current_eligible_level = level
                break
    else:
        # If no achievement, user is eligible for level 1
        for level in all_event_levels:
            if level.level == 1:
                current_eligible_level = level
                break

    # Get materials for the eligible level
    eligible_materials = []
    materials_completed_count = 0
    if current_eligible_level:
        # Query only fields that exist in the database
        raw_materials = Materials.objects.filter(
            event=event,
            level=current_eligible_level,
            status='active'
        )

        # Manually process each material to add needed properties
        for material in raw_materials:
            # Check if user completed this material
            is_completed = material.completed_users.filter(id=request.user.id).exists()


            # Create a dictionary with all needed properties
            material_dict = {
                'id': material.id,
                'title': material.title,
                'link': material.link,
                'pdf_file': material.pdf_file,
                'event': material.event,
                'level': material.level,
                'status': material.status,
                'created_at': material.created_at,
                'is_completed': is_completed,

            }

            eligible_materials.append(material_dict)

    # Calculate progress percentage
    materials_progress = 0
    total_materials = len(eligible_materials)
    if total_materials > 0:
        materials_progress = int((materials_completed_count / total_materials) * 100)

    levels_details = []
    for level in all_event_levels:
        # Check if this level has group restrictions
        level_has_group_restrictions = level.eligible_groups.exists()

        # If there are group restrictions, check if user belongs to ANY of the eligible groups
        if level_has_group_restrictions:
            # Get all eligible group IDs for this level
            level_eligible_group_ids = level.eligible_groups.values_list('id', flat=True)

            # Check if there's any overlap between user's groups and level's eligible groups
            user_in_eligible_group = False
            for group_id in user_group_ids:
                if group_id in level_eligible_group_ids:
                    user_in_eligible_group = True
                    break

            # Skip this level if user doesn't belong to any eligible group
            if not user_in_eligible_group:
                continue

        # If we reach here, either the level has no group restrictions or the user belongs to an eligible group

        # Now check achievement-based eligibility
        is_eligible = False
        is_completed = False

        if user_achievement:
            if level.level == user_achievement.level + 1:
                is_eligible = True
            elif level.level <= user_achievement.level:
                is_completed = True
        elif level.level == 1:
            is_eligible = True

        # Get available slot groups for this level (from live slots with pause status)
        slot_groups = SlotGroup.objects.filter(
            slot__slot_status='live',
            event=event,
            level=level,
            start_status='pause',  # Only get groups with pause status
            finished=False  # Exclude finished groups
        ).select_related('slot').order_by('date', 'start_time')

        # Check if user is already a participant in any active group (not ended)
        user_joined_group = None
        user_groups = SlotGroup.objects.filter(
            event=event,
            level=level,
            participants=request.user.userprofile
        ).exclude(start_status='end').exclude(finished=True).select_related('slot')

        if user_groups.exists():
            user_joined_group = user_groups.first()

        levels_details.append({
            'level': level,
            'is_eligible': is_eligible,
            'is_completed': is_completed,
            'slot_groups': slot_groups,
            'slot_groups_count': slot_groups.count(),
            'user_joined_group': user_joined_group
        })

    # Count attempts (number of participations in this event)
    attempts_count = SlotParticipant.objects.filter(
        user=request.user.userprofile,
        slot__in=Slot.objects.filter(groups__event=event)
    ).distinct().count()

    context = {
        'event': event,
        'user_achievement': user_achievement,
        'levels_details': levels_details,
        'current_level': user_achievement.level if user_achievement else 0,
        'eligible_materials': eligible_materials,
        'materials_completed_count': materials_completed_count,
        'materials_progress': materials_progress,
        'attempts_count': attempts_count,
        'current_eligible_level': current_eligible_level
    }
    return render(request, 'pages/event_details.html', context)



@login_required
def my_slots_page(request):
    current_time = datetime.now()
    highlighted_group_id = request.GET.get('highlight')

    # Find all SlotGroups that have this user as a participant
    user_slot_groups = SlotGroup.objects.filter(
        participants=request.user.userprofile,
        slot__slot_status='live'  # Only show groups from live slots
    ).select_related('slot', 'event', 'level').order_by('date', 'start_time')

    # Fetch all SlotParticipant objects for this user to avoid multiple queries
    user_participations = SlotParticipant.objects.filter(
        user=request.user.userprofile,
        slot__in=[group.slot for group in user_slot_groups]
    )

    # Create a dictionary for quick lookups
    # Key: (slot_id, group_name), Value: SlotParticipant object
    participation_dict = {(part.slot.id, part.group_name): part for part in user_participations}

    # Add participant info to each slot group
    for group in user_slot_groups:
        # Add participant data if it exists
        key = (group.slot.id, group.group_name)
        if key in participation_dict:
            participant = participation_dict[key]
            group.joined = participant.joined
            group.participant_status = participant.participant_status
        else:
            group.joined = False
            group.participant_status = None

        # Get participant count
        group.participant_count = group.participants.count()

        # Set venue information from slot
        group.venue = group.slot.venue

    # Split groups by start status
    started_groups = [group for group in user_slot_groups if group.start_status == 'start']
    paused_groups = [group for group in user_slot_groups if group.start_status == 'pause']

    context = {
        'started_slots': started_groups,  # Keep the same context variable names for compatibility
        'paused_slots': paused_groups,  # with the template
        'highlighted_group_id': highlighted_group_id
    }

    return render(request, 'pages/my_slots_page.html', context)








########################################################################################
################################################################################
##################### JOINING PAGE AREA  #####################################
################################################################################
########################################################################################

@login_required
def joining_page(request, slot_id):
    """Render the joining page for a slot."""
    # Get the slot with related data

    slot = get_object_or_404(Slot, slot_id=slot_id)

    # Get group parameter from URL (if provided)
    group_name = request.GET.get('group')

    # Get the current user's slot group
    if group_name:
        # If group_name is specified, find the matching SlotGroup
        slot_group = get_object_or_404(SlotGroup,
                                       slot=slot,
                                       group_name=group_name,
                                       participants=request.user.userprofile)
    else:
        # Find any SlotGroup for this user and slot
        try:
            slot_group = SlotGroup.objects.filter(
                slot=slot,
                participants=request.user.userprofile
            ).first()
            if not slot_group:
                return redirect('my_slots_page')
            group_name = slot_group.group_name
        except SlotGroup.DoesNotExist:
            return redirect('my_slots_page')

    if slot.slot_status != 'live' or  (slot.slot_status == 'live' and slot_group.start_status == 'paused'):
        return redirect('my_slots_page')

    group_participant_count = SlotParticipant.objects.filter(
        slot=slot,
        group_name=group_name
    ).count()

    # Get the current user's participant record
    try:
        participant = SlotParticipant.objects.get(
            slot=slot,
            group_name=group_name,
            user=request.user.userprofile
        )

        # Mark the user as joined if they weren't already
        if not participant.joined:
            participant.joined = True
            participant.save(update_fields=['joined'])
    except SlotParticipant.DoesNotExist:
        # Redirect if the user doesn't have a participant record
        return redirect('my_slots_page')

    # Get all participants in the same group
    group_members = SlotParticipant.objects.filter(
        slot=slot,
        group_name=group_name
    ).select_related('user')

    # Count joined members
    joined_count = sum(1 for member in group_members if member.joined)
    total_count = group_members.count()

    # Check if all members have joined
    all_joined = joined_count == total_count

    # Serialize group members for JavaScript
    group_members_data = [
        {
            'id': member.user.id,
            'name': member.user.name,
            'joined': member.joined
        } for member in group_members
    ]

    context = {
        'slot': slot,
        'slot_group': slot_group,
        'participant': participant,
        'group_members': group_members,
        'group_members_json': json.dumps(group_members_data),
        'joined_count': joined_count,
        'total_count': total_count,
        'all_joined': all_joined,
    }

    # Add cache prevention headers
    response = render(request, 'pages/joining_page.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


@login_required
def update_join_status(request, slot_id):
    """Update a user's join status for a slot."""
    if request.method == 'POST':
        try:
            # Get the slot
            slot = get_object_or_404(Slot, slot_id=slot_id)

            # Get group name from POST data
            group_name = request.POST.get('group_name')
            if not group_name:
                return JsonResponse({'status': 'error', 'message': 'Group name is required'}, status=400)

            # Get the specific user making the request (with select_for_update to prevent race conditions)
            participant = SlotParticipant.objects.select_for_update().get(
                slot=slot,
                group_name=group_name,
                user=request.user.userprofile
            )

            # Get leave parameter (default to True to ensure users are marked as not joined when parameter is missing)
            leave = request.POST.get('leave', 'true').lower() == 'true'

            # Update participant status
            participant.joined = not leave
            participant.save(update_fields=['joined'])  # Only update the joined field for efficiency

            # Ensure the database is updated immediately
            from django.db import transaction
            transaction.commit()

            # Add response headers to ensure no caching
            response = JsonResponse({
                'status': 'success',
                'joined': not leave
            })
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

            return response

        except SlotParticipant.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Participant not found'}, status=404)
        except Exception as e:
            # Log any other errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating join status: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def check_join_status(request, slot_id):
    """Check join status for all members in a group."""
    try:
        # Force database connection refresh to avoid stale data
        from django.db import connection
        connection.close()

        # Add cache prevention headers
        response_headers = {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }

        # Get the slot
        slot = get_object_or_404(Slot, slot_id=slot_id)

        # Get group name from query parameters
        group_name = request.GET.get('group_name')
        if not group_name:
            return JsonResponse({'status': 'error', 'message': 'Group name is required'}, status=400)

        # Get current user's participant record
        participant = SlotParticipant.objects.get(
            slot=slot,
            group_name=group_name,
            user=request.user.userprofile
        )

        # Get all members in the same group - force a fresh query
        # Use .all() and then list() to evaluate the queryset immediately
        group_members = list(SlotParticipant.objects.filter(
            slot=slot,
            group_name=group_name
        ).select_related('user'))

        # Count joined members and prepare response data
        members_data = []
        joined_count = 0
        total_count = len(group_members)

        for member in group_members:
            if member.joined:
                joined_count += 1

            members_data.append({
                'user_id': member.user.id,
                'name': member.user.name,
                'joined': member.joined
            })

        all_joined = joined_count == total_count and total_count > 0

        # Add timestamp to prevent caching
        import datetime
        timestamp = datetime.datetime.now().isoformat()

        # Get the corresponding SlotGroup status
        try:
            slot_group = SlotGroup.objects.get(slot=slot, group_name=group_name)
            group_status = slot_group.start_status
        except SlotGroup.DoesNotExist:
            group_status = 'unknown'

        return JsonResponse({
            'group_status': group_status,
            'members': members_data,
            'joined_count': joined_count,
            'total_count': total_count,
            'all_joined': all_joined,
            'timestamp': timestamp
        }, headers=response_headers)

    except (Slot.DoesNotExist, SlotParticipant.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Record not found'}, status=404)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error checking join status: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

########################################################################################
################################################################################
##################### ROOM PAGE AREA  #####################################
################################################################################
########################################################################################

def generate_group_analytics_report(slot_group, group_members):
    """
    Generate a PDF report with analytics for a specific group's voting results
    Focused on:
    1. Voting Parameters
    2. Score Component Analysis (raw, bias, absence, final)
    3. Question-wise detailed score analysis
    4. Attendance analysis
    5. Bias detection details with correct algorithm
    """
    # Create the directory for reports if it doesn't exist
    report_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(report_dir, exist_ok=True)

    # Create filename and path
    slot_id = slot_group.slot.slot_id
    group_name = slot_group.group_name
    report_filename = f"voting_analytics_{slot_id}_{group_name}.pdf"
    report_path = os.path.join(report_dir, report_filename)

    # Create the PDF document
    doc = SimpleDocTemplate(report_path, pagesize=letter)
    styles = getSampleStyleSheet()

    # Create a title style
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        spaceAfter=0.25 * inch
    )

    # Create a subtitle style
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        spaceAfter=0.15 * inch
    )

    # Create content elements
    elements = []

    # Add title and information
    elements.append(Paragraph(f"Peer Voting Analytics Report", title_style))
    elements.append(Paragraph(f"Slot: {slot_id} | Group: {group_name}", subtitle_style))
    elements.append(Spacer(1, 0.25 * inch))

    # Add voting parameters table (Section 1)
    group_size = len(group_members)
    max_ranks = determine_max_ranks(group_size)
    rank_scores = calculate_rank_scores(max_ranks)

    # Calculate average score for new penalty formulas
    avg_score = sum(rank_scores.values()) / len(rank_scores)
    bias_penalty = avg_score - 1
    absence_penalty = -(avg_score ** 2)

    elements.append(Paragraph("1. Voting Parameters", styles['Heading2']))

    params_data = [
        ["Parameter", "Value"],
        ["Group Size", str(group_size)],
        ["Maximum Ranks", str(max_ranks)],
        ["Rank Scores", str(rank_scores)],
        ["Average Score", f"{avg_score:.2f}"],
        ["Bias Penalty", f"{bias_penalty:.2f}"],
        ["Absence Penalty", f"{absence_penalty:.2f}"]
    ]

    params_table = Table(params_data, colWidths=[2.5 * inch, 3.5 * inch])
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, 1), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(params_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Find the total questions from the level
    level = slot_group.level
    question_count = 0
    for i in range(1, 13):
        question_field = f'question{i}'
        if getattr(level, question_field, '') and getattr(level, question_field, '').strip():
            question_count += 1

    # Limit to first 10 questions if needed
    question_count = min(question_count, 10)

    # Collect data for each member
    member_data = []
    absence_data = []

    # For score components chart
    total_raw_scores = []
    total_bias_penalties = []
    total_absence_penalties = []
    total_final_scores = []
    member_names = []

    # Collect all bias information for reporting
    all_bias_records = []

    for participant in group_members:
        voting_progress = getattr(participant, 'voting_progress', {}) or {}

        # Get scores for each question
        question_scores = []
        absences = []

        total_raw_score = 0
        total_bias_penalty = 0
        total_absence_penalty = 0

        for q_num in range(1, question_count + 1):
            raw_score = voting_progress.get(f'raw_score_q{q_num}', 0) or 0
            bias_penalty = voting_progress.get(f'bias_penalty_q{q_num}', 0) or 0
            absence_penalty = voting_progress.get(f'absence_penalty_q{q_num}', 0) or 0

            # Sum up totals for the chart
            total_raw_score += raw_score
            total_bias_penalty += bias_penalty
            total_absence_penalty += absence_penalty

            # Track if absent for this question
            is_absent = absence_penalty != 0
            if is_absent:
                absences.append(q_num)

            # Add question score
            question_scores.append({
                'question': q_num,
                'raw_score': raw_score,
                'bias_penalty': bias_penalty,
                'absence_penalty': absence_penalty,
                'total': raw_score + bias_penalty + absence_penalty,
                'is_absent': is_absent,
                'has_bias': bias_penalty != 0
            })

            # Collect bias details for this question
            if 'bias_details' in voting_progress and str(q_num) in voting_progress['bias_details']:
                q_bias_details = voting_progress['bias_details'][str(q_num)]

                # Add biased votes where this member was the voter
                for bias_record in q_bias_details.get('as_voter', []):
                    try:
                        record = {
                            'voter_name': participant.user.name,
                            'recipient_name': bias_record.get('recipient_name', ''),
                            'given_rank': bias_record.get('given_rank', ''),
                            'given_score': bias_record.get('given_score', ''),
                            'expected_ranks': bias_record.get('expected_ranks', []),
                            'majority_ranks': bias_record.get('majority_ranks', []),
                            'majority_scores': bias_record.get('majority_scores', []),
                            'question': q_num,
                            'bias_penalty': bias_penalty
                        }
                        all_bias_records.append(record)
                    except (KeyError, TypeError) as e:
                        print(f"Error processing bias record: {e}")
                        continue

        # Add to member data
        final_score = getattr(participant, 'mark', 0) or 0

        member_data.append({
            'member_id': participant.id,
            'name': participant.user.name,
            'scores': question_scores,
            'total_score': final_score,
            'total_raw_score': total_raw_score,
            'total_bias_penalty': total_bias_penalty,
            'total_absence_penalty': total_absence_penalty,
            'absences': absences
        })

        # Add to absence data
        absence_data.append({
            'name': participant.user.name,
            'absences': absences,
            'attendance': question_count - len(absences)
        })

        # Add to chart data
        member_names.append(participant.user.name)
        total_raw_scores.append(total_raw_score)
        total_bias_penalties.append(total_bias_penalty)
        total_absence_penalties.append(total_absence_penalty)
        total_final_scores.append(final_score)

    # Sort members by total score
    member_data.sort(key=lambda x: x['total_score'], reverse=True)

    # Section 2: Score Component Analysis (joint bar chart)
    elements.append(Paragraph("2. Score Component Analysis", styles['Heading2']))

    plt.figure(figsize=(10, 6))

    # Set up the bar chart
    x = np.arange(len(member_names))
    width = 0.2  # Width of each bar set

    fig, ax = plt.subplots(figsize=(10, 6))

    # Create bars - stacked would be confusing since bias and absence are negative
    ax.bar(x - width * 1.5, total_raw_scores, width, label='Raw Score', color='green')
    ax.bar(x - width / 2, total_bias_penalties, width, label='Bias Penalty', color='orange')
    ax.bar(x + width / 2, total_absence_penalties, width, label='Absence Penalty', color='red')
    ax.bar(x + width * 1.5, total_final_scores, width, label='Final Score', color='blue')

    # Add labels and title
    ax.set_ylabel('Score')
    ax.set_title('Score Components by Member')
    ax.set_xticks(x)
    ax.set_xticklabels([name[:10] + '...' if len(name) > 10 else name for name in member_names],
                       rotation=45, ha='right')
    ax.legend()

    # Ensure layout is clean
    fig.tight_layout()

    # Save chart to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Add chart to PDF
    img = Image(buf)
    img.drawHeight = 4 * inch
    img.drawWidth = 7 * inch
    elements.append(img)
    elements.append(Spacer(1, 0.25 * inch))

    # Add a summary table of score components
    score_components_data = [["Member", "Raw Score", "Bias Penalty", "Absence Penalty", "Final Score"]]

    for i, name in enumerate(member_names):
        score_components_data.append([
            name,
            f"{total_raw_scores[i]:.1f}",
            f"{total_bias_penalties[i]:.1f}",
            f"{total_absence_penalties[i]:.1f}",
            f"{total_final_scores[i]:.1f}"
        ])

    score_components_table = Table(score_components_data)
    score_components_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(score_components_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Section 3: Question-wise Score Analysis with Highlighting
    elements.append(Paragraph("3. Detailed Question-wise Score Analysis", styles['Heading2']))
    elements.append(Paragraph("Highlighting: Orange = Bias Penalty, Red = Absence", styles['BodyText']))
    elements.append(Spacer(1, 0.15 * inch))

    # For each member, create a detailed table
    for member in member_data:
        elements.append(Paragraph(f"Member: {member['name']}", styles['Heading3']))

        # Create table headers
        question_headers = ["Question", "Raw Score", "Bias Penalty", "Absence Penalty", "Total"]
        question_data = [question_headers]

        # Create highlighting styles for the table
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]

        # Fill table with question data
        for i, score in enumerate(member['scores']):
            row = [
                f"Q{score['question']}",
                f"{score['raw_score']:.1f}",
                f"{score['bias_penalty']:.1f}",
                f"{score['absence_penalty']:.1f}",
                f"{score['total']:.1f}"
            ]
            question_data.append(row)

            # Add highlighting for bias and absence
            row_idx = i + 1  # +1 because of header row
            if score['has_bias']:
                # Highlight bias penalty cell with orange
                table_style.append(('BACKGROUND', (2, row_idx), (2, row_idx), colors.orange))

            if score['is_absent']:
                # Highlight absence penalty cell with red
                table_style.append(('BACKGROUND', (3, row_idx), (3, row_idx), colors.red))

        # Create and style the table
        question_table = Table(question_data)
        question_table.setStyle(TableStyle(table_style))

        elements.append(question_table)
        elements.append(Spacer(1, 0.25 * inch))

    # Section 4: Question Attendance Analysis
    elements.append(Paragraph("4. Question Attendance Analysis", styles['Heading2']))

    # Create a table showing which questions each user missed
    attendance_header = ["Member"] + [f"Q{i}" for i in range(1, question_count + 1)]
    attendance_data = [attendance_header]

    # Attendance table styles
    attendance_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]

    for member_idx, member in enumerate(member_data):
        # Create row with member name first
        row = [member['name']]

        # Add attendance markers for each question
        for q_num in range(1, question_count + 1):
            if q_num in member['absences']:
                row.append("×")  # Absent
                # Mark absent cells with red background
                attendance_style.append((
                    'BACKGROUND',
                    (q_num, member_idx + 1),
                    (q_num, member_idx + 1),
                    colors.red
                ))
            else:
                row.append("✓")  # Present
                # Mark present cells with light green background
                attendance_style.append((
                    'BACKGROUND',
                    (q_num, member_idx + 1),
                    (q_num, member_idx + 1),
                    colors.lightgreen
                ))

        attendance_data.append(row)

    # Create attendance table
    attendance_table = Table(attendance_data)
    attendance_table.setStyle(TableStyle(attendance_style))

    elements.append(attendance_table)

    # Add a legend for attendance table
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph("Legend: ✓ = Present, × = Absent", styles['BodyText']))

    # Section 5: Bias Detection Details - UPDATED to match the correct algorithm
    elements.append(Paragraph("5. Bias Detection Details", styles['Heading2']))
    elements.append(Paragraph(
        "**Bias Detection Algorithm:** Votes are considered biased when a voter gives a rank that doesn't match what the majority of voters gave. Majority is determined by the most frequently assigned ranks.",
        styles['BodyText']))
    elements.append(Spacer(1, 0.15 * inch))

    # Create a table to show biasing details with simplified columns
    bias_headers = ["Voter", "Recipient", "Question", "Given Rank", "Majority Scores", "Bias Detected"]
    bias_data = [bias_headers]

    # Table style
    bias_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]

    # Sort bias records by voter, then question, then recipient for better organization
    all_bias_records.sort(key=lambda x: (x['voter_name'], x['question'], x['recipient_name']))

    # Add all records to the table data
    for record in all_bias_records:
        # Format the data for the table
        majority_scores_str = f"[{', '.join(map(str, record['majority_scores']))}]"

        row = [
            record['voter_name'],
            record['recipient_name'],
            f"Q{record['question']}",  # Add question number
            f"{record['given_rank']} ({record['given_score']} pts)",
            majority_scores_str,
            "**Yes**"  # Bold "Yes" as in your example
        ]
        bias_data.append(row)

    # If there are no bias records, add a note
    if not all_bias_records:
        elements.append(Paragraph("No bias penalties were applied for this group.", styles['BodyText']))
    else:
        # Create and style the bias table - adjusted column widths for the simplified table
        bias_table = Table(bias_data,
                           colWidths=[1.2 * inch, 1.2 * inch, 0.8 * inch, 1.0 * inch, 1.0 * inch, 0.8 * inch])
        bias_table.setStyle(TableStyle(bias_style))
        elements.append(bias_table)

    elements.append(Spacer(1, 0.25 * inch))

    # Add explanation of how bias is calculated - updated to match correct algorithm
    elements.append(Paragraph("How Bias is Determined:", styles['Heading4']))
    bias_explanation = """
    Bias is detected when a voter gives a rank that doesn't match what the majority of voters gave:

    1. For each recipient, we collect all ranks they received from different voters
    2. We identify the most commonly assigned rank(s) - these become the 'majority ranks'
    3. Any voter who assigned a different rank than the majority is considered to have given a biased vote
    4. Each voter who gave biased votes receives a penalty of %.2f points

    This approach helps identify outlier votes that differ from the consensus of the group.
    """ % (bias_penalty)
    elements.append(Paragraph(bias_explanation, styles['BodyText']))

    elements.append(Spacer(1, 0.25 * inch))

    # Build PDF
    doc.build(elements)

    # Return the path to the generated report
    return report_filename

@login_required
def download_report(request, report_filename):

    try:
        # Parse the filename to extract slot_id
        filename_parts = report_filename.split('_')
        if len(filename_parts) < 3 or not filename_parts[0] == 'voting' or not filename_parts[1] == 'analytics':
            return HttpResponse("Invalid report filename format", status=400)

        slot_id = filename_parts[2]  # Get the slot_id part

        # Get the slot
        try:
            slot = Slot.objects.get(slot_id=slot_id)
        except Slot.DoesNotExist:
            return HttpResponse("Slot not found", status=404)

        # Check if the current user is the creator or assignee of the slot
        is_authorized = (
                request.user.is_superuser or  # Superadmins can always access
                slot.created_by == request.user.userprofile or  # Creator check
                slot.assigned_to == request.user.userprofile  # Assignee check
        )

        if not is_authorized:
            return HttpResponse("You don't have permission to view this report", status=403)

        # If authorized, serve the file
        report_path = os.path.join(settings.MEDIA_ROOT, 'reports', report_filename)
        if os.path.exists(report_path):
            return FileResponse(open(report_path, 'rb'), content_type='application/pdf')
        else:
            return HttpResponse("Report not found", status=404)

    except Exception as e:
        import traceback
        print(f"Error serving report: {str(e)}")
        print(traceback.format_exc())
        return HttpResponse("Error processing report request", status=500)


##########################################################################################
##########################################################################################


def determine_max_ranks(group_size):
    """
    Determine the maximum number of ranks based on group size.
    """
    if 6 <= group_size <= 11:
        return 2
    elif 12 <= group_size <= 17:
        return 3
    elif 18 <= group_size <= 23:
        return 4
    elif 24 <= group_size <= 29:
        return 5
    elif group_size >= 30:
        return 6
    else:
        # Default fallback - should never happen with validation
        return 1


def calculate_rank_scores(max_ranks):
    """
    Calculate scores for each rank position.
    """
    # Create scoring dictionary - Rank 1 gets max_ranks points, rank 2 gets max_ranks-1, etc.
    rank_scores = {}
    for rank in range(1, max_ranks + 1):
        rank_scores[rank] = max_ranks - rank + 1

    return rank_scores


def calculate_marks_for_question(slot_group, group_members, question_number=None):
    try:
        # Get group size
        group_size = len(group_members)

        # Determine max ranks based on group size
        def determine_max_ranks(size):
            if 6 <= size <= 11:
                return 2
            elif 12 <= size <= 17:
                return 3
            elif 18 <= size <= 23:
                return 4
            elif 24 <= size <= 29:
                return 5
            elif size >= 30:
                return 6
            return 2  # Default fallback

        max_ranks = determine_max_ranks(group_size)

        # Calculate rank scores
        def calculate_rank_scores(max_ranks):
            return {rank: max_ranks - rank + 1 for rank in range(1, max_ranks + 1)}

        rank_scores = calculate_rank_scores(max_ranks)

        # Calculate average score for penalty calculations
        avg_score = sum(rank_scores.values()) / len(rank_scores)

        # Penalty calculations
        BIAS_PENALTY = avg_score - 1
        ABSENCE_PENALTY = -1 * (avg_score ** 2)

        # Print voting system parameters
        print("\n===== VOTING SYSTEM PARAMETERS =====")
        print(f"Slot ID: {slot_group.slot.slot_id}")
        print(f"Group Name: {slot_group.group_name}")
        print(f"Group Size: {group_size} members")
        print(f"Maximum Ranks Allowed: {max_ranks}")
        print(f"Rank Scores: {rank_scores}")
        print(f"Average Score: {avg_score:.2f}")
        print(f"Bias Penalty: {BIAS_PENALTY:.2f}")
        print(f"Absence Penalty: {ABSENCE_PENALTY:.2f}")
        print("=====================================\n")

        # If no specific question number, calculate final results
        if question_number is None:
            # Calculate overall scores for all members
            for participant in group_members:
                total_mark = 0
                voting_progress = participant.voting_progress or {}

                # Sum up scores from all questions
                print(f"Calculating final mark for {participant.user.name}:")
                for q_num in range(1, 20):  # Assuming max 20 questions
                    q_mark_key = f'marks_q{q_num}'
                    if q_mark_key in voting_progress:
                        q_mark = voting_progress.get(q_mark_key, 0) or 0
                        print(f"  Question {q_num}: {q_mark} points")
                        total_mark += q_mark

                # Save final mark
                participant.mark = total_mark
                participant.save(update_fields=['mark'])
                print(f"Final mark for {participant.user.name}: {total_mark}")

            return True

        # Process specific question
        print(f"Calculating marks for question {question_number}")

        # Enhanced bias and absence tracking
        bias_details = {}
        absence_details = {}
        detailed_voting_patterns = {}

        # Prepare votes tracking
        votes = {}
        for member in group_members:
            votes[str(member.id)] = {
                'given': {},
                'received': {},
                'voters': set(),
                'non_voters': set()
            }

        # Collect votes with detailed tracking - UPDATED TO HANDLE ALL RANKS
        for member in group_members:
            member_id = str(member.id)
            voting_progress = member.voting_progress or {}

            # Extract rankings for this question
            rankings = voting_progress.get(f'question_{question_number}', {})

            # Check for minimum required rankings (at least rank1 must exist)
            if not rankings or 'rank1' not in rankings:
                absence_details[member_id] = {
                    'name': member.user.name,
                    'reason': 'No valid rankings submitted',
                    'penalty': ABSENCE_PENALTY
                }
                continue

            # Process all ranks that exist
            ranks_found = 0
            for rank_num in range(1, max_ranks + 1):
                rank_key = f'rank{rank_num}'
                if rank_key in rankings and rankings[rank_key]:  # Check that the rank exists and is not empty
                    recipient_id = str(rankings[rank_key])

                    # Record given and received votes
                    votes[member_id]['given'][recipient_id] = rank_num
                    votes[recipient_id]['received'][member_id] = rank_num
                    ranks_found += 1

            # If insufficient ranks were submitted, mark as absent
            if ranks_found < max_ranks:
                absence_details[member_id] = {
                    'name': member.user.name,
                    'reason': f'Submitted only {ranks_found}/{max_ranks} required ranks',
                    'penalty': ABSENCE_PENALTY
                }

        # Detailed voting pattern analysis
        for voter in group_members:
            voter_id = str(voter.id)
            for recipient in group_members:
                recipient_id = str(recipient.id)

                # Skip self-voting
                if voter_id == recipient_id:
                    continue

                # Check if voter voted for recipient
                voted = False
                for vote_type, vote_value in votes[voter_id]['given'].items():
                    if vote_type == recipient_id:
                        voted = True
                        break

                # Track voters and non-voters
                if voted:
                    votes[recipient_id]['voters'].add(voter_id)
                else:
                    votes[recipient_id]['non_voters'].add(voter_id)

        # Calculate raw scores
        raw_scores = {}
        for member_id, vote_data in votes.items():
            member_score = 0
            for _, rank in vote_data['received'].items():
                member_score += rank_scores.get(rank, 0)

            raw_scores[member_id] = member_score

            # Prepare detailed voting pattern for each member
            detailed_voting_patterns[member_id] = {
                'name': next((m.user.name for m in group_members if str(m.id) == member_id), 'Unknown'),
                'total_voters': len(vote_data['voters']),
                'total_non_voters': len(vote_data['non_voters']),
                'non_voters': [
                    next((m.user.name for m in group_members if str(m.id) == voter_id), 'Unknown')
                    for voter_id in vote_data['non_voters']
                ]
            }

        # BIAS DETECTION ALGORITHM
        # For each recipient, analyze the ranks they received and identify biased votes
        biased_votes = []  # Store detailed information about each biased vote
        biased_voters = set()  # Track which voters gave biased votes

        # For each member (as recipient)
        for recipient_id, vote_data in votes.items():
            # Skip members with no received votes or absent members
            if not vote_data['received'] or recipient_id in absence_details:
                continue

            # Collect all ranks this recipient received
            received_ranks = []
            voter_ranks = {}  # Map of voter_id to rank they gave

            for voter_id, rank in vote_data['received'].items():
                # Skip absent voters
                if voter_id in absence_details:
                    continue
                received_ranks.append(rank)
                voter_ranks[voter_id] = rank

            if not received_ranks:
                continue  # No valid ranks after filtering

            # Count frequency of each rank
            rank_counts = {}
            for rank in received_ranks:
                rank_counts[rank] = rank_counts.get(rank, 0) + 1

            # Find the majority rank - the most frequent rank
            if not rank_counts:
                continue

            max_frequency = max(rank_counts.values())
            majority_ranks = [rank for rank, count in rank_counts.items() if count == max_frequency]

            # If there's a tie for most frequent rank, we need a tiebreaker
            # For simplicity, we'll use the lowest rank as the majority rank in case of ties
            expected_ranks = majority_ranks.copy()  # Keep track of original majority ranks for reporting
            if len(majority_ranks) > 1:
                majority_ranks = [min(majority_ranks)]

            # Get scores for majority ranks
            majority_scores = [rank_scores[rank] for rank in
                               expected_ranks]  # Use expected_ranks for complete reporting

            # Check each vote this recipient received
            for voter_id, given_rank in voter_ranks.items():
                # If the given rank is not in the majority ranks, it's biased
                if given_rank not in majority_ranks:
                    # Add voter to biased voters set
                    biased_voters.add(voter_id)

                    # Store detailed information about this biased vote
                    biased_votes.append({
                        'voter_id': voter_id,
                        'voter_name': next((m.user.name for m in group_members if str(m.id) == voter_id), 'Unknown'),
                        'recipient_id': recipient_id,
                        'recipient_name': next((m.user.name for m in group_members if str(m.id) == recipient_id),
                                               'Unknown'),
                        'given_rank': given_rank,
                        'given_score': rank_scores[given_rank],
                        'majority_ranks': majority_ranks,
                        'majority_scores': majority_scores,
                        'expected_ranks': expected_ranks,  # Include all tied ranks for reporting
                        'bias_penalty': BIAS_PENALTY
                    })

                    # Add to bias details for reporting
                    if voter_id not in bias_details:
                        bias_details[voter_id] = {
                            'name': next((m.user.name for m in group_members if str(m.id) == voter_id), 'Unknown'),
                            'biased_votes': [],
                            'penalty': BIAS_PENALTY
                        }

                    bias_details[voter_id]['biased_votes'].append({
                        'recipient_name': next((m.user.name for m in group_members if str(m.id) == recipient_id),
                                               'Unknown'),
                        'given_rank': given_rank,
                        'majority_ranks': expected_ranks,  # Include all tied ranks for reporting
                        'majority_scores': majority_scores
                    })

        # Print Bias Detection Details
        print("\nBias Detection Details:")
        if biased_votes:
            print(f"Found {len(biased_votes)} biased votes from {len(biased_voters)} unique voters")
            for vote in biased_votes:
                print(f"\nVoter: {vote['voter_name']} (ID: {vote['voter_id']})")
                print(f"  Recipient: {vote['recipient_name']} (ID: {vote['recipient_id']})")
                print(f"  Given Rank: {vote['given_rank']} (Score: {vote['given_score']})")
                print(f"  Expected Ranks: {vote['expected_ranks']}")
                print(f"  Majority Scores: {vote['majority_scores']}")
                print(f"  Bias Penalty: {BIAS_PENALTY}")
        else:
            print("No bias detected in this question.")

        # Print Absence Details
        print("\nAbsence Analysis:")
        if absence_details:
            for member_id, details in absence_details.items():
                print(f"\nMember {details['name']} (ID: {member_id}):")
                print(f"  Absence Reason: {details['reason']}")
                print(f"  Absence Penalty: {details['penalty']}")
        else:
            print("All members submitted valid rankings.")

        # Calculate final scores with the new bias penalty application
        final_scores = {}
        for member_id, raw_score in raw_scores.items():
            # Apply absence penalty if applicable
            if member_id in absence_details:
                final_scores[member_id] = ABSENCE_PENALTY
                continue

            # Apply bias penalty if this voter gave any biased votes
            if member_id in biased_voters:
                final_scores[member_id] = raw_score - BIAS_PENALTY
            else:
                final_scores[member_id] = raw_score

        # Update voting progress
        for member in group_members:
            member_id = str(member.id)
            voting_progress = member.voting_progress or {}

            # Store question-specific marks and additional data
            voting_progress[f'raw_score_q{question_number}'] = raw_scores.get(member_id, 0)
            voting_progress[f'bias_penalty_q{question_number}'] = -BIAS_PENALTY if member_id in biased_voters else 0
            voting_progress[
                f'absence_penalty_q{question_number}'] = ABSENCE_PENALTY if member_id in absence_details else 0
            voting_progress[f'marks_q{question_number}'] = final_scores.get(member_id, 0)

            # Store bias votes for reporting
            if not voting_progress.get('bias_details'):
                voting_progress['bias_details'] = {}

            # Store biased votes where this member was the voter
            voter_biased_votes = [vote for vote in biased_votes if vote['voter_id'] == member_id]
            if voter_biased_votes:
                voting_progress['bias_details'][str(question_number)] = {
                    'as_voter': [
                        {
                            'question': question_number,
                            'recipient_id': vote['recipient_id'],
                            'recipient_name': vote['recipient_name'],
                            'given_rank': vote['given_rank'],
                            'given_score': vote['given_score'],
                            'majority_ranks': vote['expected_ranks'],  # Use expected_ranks for complete reporting
                            'majority_scores': vote['majority_scores'],
                            'expected_ranks': vote['expected_ranks']
                        }
                        for vote in voter_biased_votes
                    ]
                }

            # Calculate total accumulated mark
            total_mark = 0
            for q_num in range(1, 20):
                q_mark_key = f'marks_q{q_num}'
                if q_mark_key in voting_progress:
                    q_mark = voting_progress.get(q_mark_key, 0) or 0
                    total_mark += q_mark

            # Update member's mark and voting progress
            member.mark = total_mark
            member.voting_progress = voting_progress
            member.save()

            # Logging
            print(f"\nUpdated marks for {member.user.name}:")
            print(f"  Raw score: {raw_scores.get(member_id, 0)}")
            print(f"  Bias penalty: {'-' + str(BIAS_PENALTY) if member_id in biased_voters else '0'}")
            print(f"  Absence penalty: {ABSENCE_PENALTY if member_id in absence_details else '0'}")
            print(f"  Final score for Q{question_number}: {final_scores.get(member_id, 0)}")
            print(f"  Total accumulated mark: {total_mark}")

        return True

    except Exception as e:
        import traceback
        print(f"Error calculating marks: {str(e)}")
        print(traceback.format_exc())
        return False

def has_valid_votes(voting_progress, question_number):
    """
    Check if the voting progress contains valid votes for a question.
    Validates based on the number of votes against the maximum allowed for the group size.

    Parameters:
    voting_progress (dict): The voting progress dictionary
    question_number (int): The question number to check

    Returns:
    bool: True if voting progress has valid votes, False otherwise
    """
    if not voting_progress:
        return False

    # Check format 1: Direct question_{number} entry
    question_key = f'question_{question_number}'
    if question_key in voting_progress:
        rankings = voting_progress[question_key]
        if rankings and isinstance(rankings, dict) and any(k.startswith('rank') for k in rankings.keys()):
            return True

    # Check format 2: Votes array entry
    if 'votes' in voting_progress and str(question_number) in voting_progress['votes']:
        votes_entry = voting_progress['votes'][str(question_number)]
        if votes_entry and 'rankings' in votes_entry and votes_entry['rankings']:
            return True

    # Check format 3: Direct question number as key
    direct_key = f'question{question_number}'
    if direct_key in voting_progress:
        rankings = voting_progress[direct_key]
        if rankings and isinstance(rankings, dict) and any(k.startswith('rank') for k in rankings.keys()):
            return True

    # Check if explicitly marked as absent (counts as "voted" for completion status)
    if f'is_absent_q{question_number}' in voting_progress and voting_progress[f'is_absent_q{question_number}']:
        return True

    return False




######


@login_required
def room_page(request, slot_id):
    """
    Comprehensive view for the room page that handles all aspects of the voting process.
    """
    # Check if this is an AJAX request
    is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    try:
        # Get the slot with error handling
        slot = get_object_or_404(Slot, slot_id=slot_id)

        # Check if slot is live
        if slot.slot_status != 'live':
            message = 'Sorry, could not join group room. Slot is not active.'
            return JsonResponse({'status': 'error', 'message': message}, status=403) if is_ajax_request else render(
                request, 'pages/error.html', {'error_message': message}
            )

        # Get group name from query parameters
        group_name = request.GET.get('group')

        # Find user's group if no group name provided
        if not group_name:
            user_groups = SlotGroup.objects.filter(
                slot=slot,
                participants=request.user.userprofile
            )
            if user_groups.exists():
                group_name = user_groups.first().group_name
            else:
                message = 'Sorry, could not join group room. You are not assigned to any group in this slot.'
                return JsonResponse({'status': 'error', 'message': message}, status=403) if is_ajax_request else render(
                    request, 'pages/error.html', {'error_message': message}
                )

        # Get and validate SlotGroup
        slot_group = get_object_or_404(SlotGroup, slot=slot, group_name=group_name)


        # Check if user is part of this group
        if request.user.userprofile not in slot_group.participants.all():
            message = 'Sorry, could not join group room. You are not a participant in this group.'
            return JsonResponse({'status': 'error', 'message': message}, status=403) if is_ajax_request else render(
                request, 'pages/error.html', {'error_message': message}
            )

        if slot_group.start_status == 'pause':
            message = 'Access denied. This group is currently paused. Please wait for the instructor to start the session.'
            return JsonResponse({'status': 'error', 'message': message}, status=403) if is_ajax_request else render(
                request, 'pages/error.html', {'error_title': 'Access Denied', 'error_message': message}
            )


        # Get participant record or create it if it doesn't exist
        try:
            participant = SlotParticipant.objects.get(
                slot=slot,
                group_name=group_name,
                user=request.user.userprofile
            )

            # Check if results have been published to redirect to results page
            results_published = (participant.voting_progress and
                                 participant.voting_progress.get('results_published', False))

            if results_published and not is_ajax_request:
                from django.shortcuts import redirect
                from django.urls import reverse
                return redirect(reverse('session_results', kwargs={'slot_id': slot_id}) + f'?group={group_name}')

        except SlotParticipant.DoesNotExist:
            # Create a new participant record
            participant = SlotParticipant.objects.create(
                slot=slot,
                group_name=group_name,
                user=request.user.userprofile,
                joined=True
            )

        # Auto-join if not already joined
        if not participant.joined:
            participant.joined = True
            participant.save(update_fields=['joined'])

        # --- AJAX HANDLERS ---
        if is_ajax_request:
            # For status updates via GET
            if request.method == 'GET' and request.GET.get('action') == 'status_update':
                try:
                    # Add a flag to check if the client has manually finished voting
                    check_results_only = request.GET.get('check_results_only') == 'true'

                    # If the user has manually finished voting, only check if results are published
                    if check_results_only:
                        # Simplified response with just results status
                        voting_progress = participant.voting_progress or {}
                        results_published = voting_progress.get('results_published', False)

                        response_data = {
                            'status': 'success',
                            'results_published': results_published,
                            'voting_status': participant.voting_status
                        }

                        # Add redirect URL if results are published
                        if results_published:
                            from django.urls import reverse
                            response_data['redirect_url'] = reverse('session_results',
                                                                    kwargs={
                                                                        'slot_id': slot.slot_id}) + f'?group={group_name}'

                        return JsonResponse(response_data)
                    else:
                        # Regular full status response
                        return get_room_status_response(slot, slot_group, participant, group_name)
                except Exception as e:
                    import traceback
                    print(f"Error in status update: {str(e)}")
                    print(traceback.format_exc())
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Error updating status: {str(e)}'
                    }, status=500)

            # Handle various POST actions
            if request.method == 'POST':
                action = request.POST.get('action')

                try:
                    # Request voting action
                    # Request voting action
                    if action == 'request_voting':
                        try:
                            # CRITICAL: Re-query to ensure we have the right participant
                            participant = SlotParticipant.objects.get(
                                slot=slot,
                                group_name=group_name,
                                user=request.user.userprofile
                            )

                            participant.request_voting = 'request'
                            participant.voting_status = 'in_progress'  # Set status to in_progress
                            participant.save(update_fields=['request_voting', 'voting_status'])

                            print(
                                f"Requested voting for user {participant.user.name} in slot {slot.slot_id}, group {group_name}")

                            return JsonResponse({
                                'status': 'success',
                                'message': 'Voting request submitted successfully',
                                'slot_id': slot.slot_id,
                                'group_name': group_name
                            })
                        except SlotParticipant.DoesNotExist:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Could not find your participant record for this group'
                            }, status=404)

                    # Submit rankings for a question
                    elif action == 'submit_rankings':
                        return handle_submit_rankings(request, slot, participant, group_name)

                    # Move to next question

                    # Move to next question
                    elif action == 'next_question':
                        try:
                            # Get the specific participant ID from the POST request
                            participant_id = int(request.POST.get('participant_id', 0))

                            # IMPORTANT: Query by primary key to ensure we get EXACTLY one record
                            participant = SlotParticipant.objects.get(
                                id=participant_id,  # Use the exact ID
                                slot=slot,  # Still verify slot
                                group_name=group_name,  # Still verify group
                                user=request.user.userprofile  # Still verify user
                            )

                            current_question = int(request.POST.get('current_question', 1))

                            # Update voting progress with a fresh dictionary to avoid shared references
                            voting_progress = {} if participant.voting_progress is None else dict(
                                participant.voting_progress)
                            voting_progress['current_question'] = current_question + 1

                            # Save ONLY this record by using the primary key
                            SlotParticipant.objects.filter(id=participant_id).update(
                                voting_progress=voting_progress
                            )

                            # Log the specific update
                            print(
                                f"Updated current_question to {current_question + 1} for participant ID {participant_id}")
                            print(
                                f"Participant details: {participant.user.name}, slot {slot.slot_id}, group {group_name}")

                            return JsonResponse({
                                'status': 'success',
                                'message': f'Advanced to question {current_question + 1}',
                                'current_question': current_question + 1,
                                'slot_id': slot.slot_id,
                                'group_name': group_name
                            })
                        except SlotParticipant.DoesNotExist:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Could not find your specific participant record'
                            }, status=404)

                    # Mark user as absent for a question
                    # Mark user as absent for a question
                    elif action == 'mark_absent':
                        try:
                            # CRITICAL: Re-query to ensure we have the right participant
                            participant = SlotParticipant.objects.get(
                                slot=slot,
                                group_name=group_name,
                                user=request.user.userprofile
                            )

                            question_index = int(request.POST.get('question_index', 1))
                            voting_progress = participant.voting_progress or {}

                            # Store absence information
                            voting_progress[f'question_{question_index}'] = {}
                            voting_progress[f'is_absent_q{question_index}'] = True

                            # Update current question if needed
                            current_question = int(voting_progress.get('current_question', 1))
                            if question_index >= current_question:
                                voting_progress['current_question'] = question_index + 1

                            participant.voting_progress = voting_progress
                            participant.save(update_fields=['voting_progress'])

                            print(f"Marked absent for question {question_index} for user {participant.user.name} in slot {slot.slot_id}, group {group_name}")

                            return JsonResponse({
                                'status': 'success',
                                'message': 'You have been marked as absent for this question',
                                'is_absent': True,
                                'current_question': voting_progress.get('current_question', 1),
                                'slot_id': slot.slot_id,
                                'group_name': group_name
                            })
                        except SlotParticipant.DoesNotExist:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Could not find your participant record for this group'
                            }, status=404)

                    # Complete voting process - SIMPLIFIED
                    elif action == 'complete_voting':
                        try:
                            # Get the specific participant ID from the request
                            participant_id = int(request.POST.get('participant_id', 0))

                            # Query by exact ID to ensure we update ONLY this specific participant record
                            participant = SlotParticipant.objects.get(
                                id=participant_id,
                                slot=slot,
                                group_name=group_name,
                                user=request.user.userprofile
                            )

                            # Update voting status directly in the database using the participant ID
                            SlotParticipant.objects.filter(id=participant_id).update(
                                voting_status='finished'
                            )

                            # Also update the voting_progress field with manually_completed flag
                            voting_progress = {} if participant.voting_progress is None else dict(
                                participant.voting_progress)
                            voting_progress['manually_completed'] = True

                            SlotParticipant.objects.filter(id=participant_id).update(
                                voting_progress=voting_progress
                            )

                            # Log after update for confirmation
                            print(f"Successfully marked voting as completed for participant ID {participant_id}")

                            return JsonResponse({
                                'status': 'success',
                                'message': 'Voting completed successfully',
                                'voting_status': 'finished',
                                'slot_id': slot.slot_id,
                                'group_name': group_name,
                                'participant_id': participant_id
                            })
                        except SlotParticipant.DoesNotExist:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Could not find your specific participant record'
                            }, status=404)

                    elif action == 'get_group_members':
                        # Get all participants in the same group
                        try:
                            group_members = SlotParticipant.objects.filter(
                                slot=slot,
                                group_name=group_name
                            ).select_related('user')

                            # Prepare member data for JSON response
                            members_data = []
                            for member in group_members:
                                member_info = {
                                    'id': member.id,
                                    'name': member.user.name,
                                    'joined': member.joined,
                                    'roll_number': getattr(member.user, 'roll_number', ''),
                                    'staff_id': getattr(member.user, 'staff_id', ''),
                                    'photo_url': member.user.photo.url if hasattr(member.user,
                                                                                  'photo') and member.user.photo else None
                                }
                                members_data.append(member_info)

                            return JsonResponse({
                                'status': 'success',
                                'members': members_data
                            })
                        except Exception as e:
                            import traceback
                            print(f"Error getting group members: {str(e)}")
                            print(traceback.format_exc())
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Error retrieving group members: {str(e)}'
                            }, status=500)

                    # Save notes (additional feature)
                    elif action == 'save_notes':
                        notes_content = request.POST.get('notes_content', '')
                        # Don't save in voting_progress
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Notes saved successfully'
                        })

                    # Default for unknown action
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Unknown action: {action}'
                    }, status=400)

                except Exception as e:
                    import traceback
                    print(f"Error processing action {action}: {str(e)}")
                    print(traceback.format_exc())
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Error processing action: {str(e)}'
                    }, status=500)
        # --- PREPARE DATA FOR TEMPLATE ---

        # Get all participants in the same group
        group_members = SlotParticipant.objects.filter(
            slot=slot,
            group_name=group_name
        ).select_related('user')

        # Calculate group parameters based on size
        group_size = group_members.count()
        max_ranks = determine_max_ranks(group_size)
        rank_scores = calculate_rank_scores(max_ranks)

        # Calculate average score
        avg_score = sum(rank_scores.values()) / len(rank_scores)

        # Calculate penalties using new formulas
        bias_penalty = avg_score - 1
        absence_penalty = -(avg_score ** 2)

        # Retrieve the topic for this group
        assigned_topic = slot_group.topic

        # Get the questions for this level
        level = slot_group.level
        level_questions = []
        for i in range(1, 13):  # question1 through question12
            question_field = f'question{i}'
            question_text = getattr(level, question_field, '')
            if question_text and question_text.strip():  # Only include non-empty questions
                level_questions.append({
                    'question_number': i,
                    'question_text': question_text
                })
        level_questions = level_questions[:10]  # Limit to first 10 questions

        # Get current question number from participant's voting status
        current_question = 1
        voting_data = {}

        try:
            # Check if participant has saved voting progress
            if hasattr(participant, 'voting_progress') and participant.voting_progress:
                voting_data = participant.voting_progress
                current_question = int(voting_data.get('current_question', 1))

                # POTENTIAL ISSUE: This might be updating all records
                if 'voting_parameters' not in voting_data:
                    # Re-query to ensure correct participant
                    participant = SlotParticipant.objects.get(
                        slot=slot,
                        group_name=group_name,
                        user=request.user.userprofile
                    )

                    voting_data = participant.voting_progress or {}
                    voting_data['voting_parameters'] = {
                        'group_size': group_size,
                        'max_ranks': max_ranks,
                        'rank_scores': rank_scores,
                        'average_score': avg_score,
                        'bias_penalty': bias_penalty,
                        'absence_penalty': absence_penalty
                    }
                    participant.voting_progress = voting_data
                    participant.save(update_fields=['voting_progress'])


        except (AttributeError, ValueError, TypeError):
            # Handle case where voting_progress doesn't exist or is invalid
            voting_data = {
                'current_question': 1,
                'voting_parameters': {
                    'slot_id': slot.slot_id,
                    'group_name': group_name,
                    'group_size': group_size,
                    'max_ranks': max_ranks,
                    'rank_scores': rank_scores,
                    'average_score': avg_score,
                    'bias_penalty': bias_penalty,
                    'absence_penalty': absence_penalty
                }
            }

        # Check user's individual voting progress for each question
        question_voting_statuses = {}
        for q_num in range(1, len(level_questions) + 1):
            # Check if this user has voted for this question
            has_voted = has_valid_votes(participant.voting_progress or {}, q_num)
            question_voting_statuses[q_num] = has_voted

        # Get the total number of questions that should be completed
        total_questions = len(level_questions)

        # Update the user's voting status if all questions are completed
        if current_question > total_questions and participant.voting_status != 'finished':
            participant.voting_status = 'finished'
            participant.save(update_fields=['voting_status'])

        # Check if current user has completed voting
        voting_completed = current_question > total_questions and total_questions > 0

        # Check if results have been published
        results_published = False
        if hasattr(participant, 'voting_progress') and participant.voting_progress:
            results_published = participant.voting_progress.get('results_published', False)

        # Get ranked members for results display only if results are published
        ranked_members = []
        user_rank = 0

        if results_published:
            # Sort members by mark (descending)
            ranked_members = sorted(
                group_members,
                key=lambda m: getattr(m, 'mark', 0) or 0,
                reverse=True
            )

            # Find current user's rank
            for idx, member in enumerate(ranked_members):
                if member.id == participant.id:
                    user_rank = idx + 1
                    break

            # Assign the user's rank to the participant for template use
            participant.user_rank = user_rank

        # Overall group voting status
        group_voting_in_progress = participant.voting_status == 'in_progress'

        # Get saved notes if any
        saved_notes = ''
        if hasattr(participant, 'voting_progress') and participant.voting_progress:
            saved_notes = participant.voting_progress.get('notes', '')

        # --- RENDER TEMPLATE ---
        context = {
            'slot': slot,
            'slot_group': slot_group,
            'participant': participant,
            'group_members': group_members,
            'assigned_topic': assigned_topic,
            'level_questions': level_questions,
            'group_voting_in_progress': group_voting_in_progress,
            'user_profile': request.user.userprofile,
            'current_question': current_question,
            'question_voting_statuses': question_voting_statuses,
            'voting_completed': voting_completed,
            'results_published': results_published,
            'ranked_members': ranked_members,
            'user_mark': getattr(participant, 'mark', 0) or 0,
            'user_rank': user_rank,
            'saved_notes': saved_notes,
            'voting_parameters': {
                'slot_id': slot.slot_id,
                'group_name': group_name,
                'group_size': group_size,
                'max_ranks': max_ranks,
                'rank_scores': rank_scores,
                'average_score': avg_score,
                'bias_penalty': bias_penalty,
                'absence_penalty': absence_penalty
            }
        }

        return render(request, 'pages/room_page.html', context)

    except Exception as e:
        import traceback
        print(f"Error in room_page: {str(e)}")
        print(traceback.format_exc())

        # Return JSON for AJAX requests, HTML for regular requests
        if is_ajax_request:
            return JsonResponse({
                'status': 'error',
                'message': f'An error occurred: {str(e)}'
            }, status=500)
        else:
            return render(request, 'pages/error.html', {
                'error_message': f'An unexpected error occurred: {str(e)}'
            })


def handle_submit_rankings(request, slot, participant, group_name):
    """
    Process submitted rankings for a question with strict slot/group validation
    """
    try:
        # Extract question index and rankings from POST data
        try:
            question_index = int(request.POST.get('question_index', 1))


        except (TypeError, ValueError):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid question index'
            }, status=400)

        # CRITICAL FIX: Always re-query to ensure we have the exact participant for this slot and group
        try:
            participant_id = int(request.POST.get('participant_id', 0))
            participant = SlotParticipant.objects.get(
                id=participant_id,
                slot=slot,
                group_name=group_name,
                user=request.user.userprofile
            )
        except SlotParticipant.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Could not find your participant record for this specific group and slot'
            }, status=404)

        # Log to confirm the correct participant is being used
        print(f"Saving rankings for user {participant.user.name} in slot {slot.slot_id}, group {group_name}, question {question_index}")

        # Extract rankings, ensuring they are valid
        rankings = {}
        for key, value in request.POST.items():
            if key.startswith('rank'):
                try:
                    rank = int(key.replace('rank', ''))
                    member_id = int(value)
                    rankings[f'rank{rank}'] = member_id
                except (ValueError, TypeError):
                    continue  # Skip invalid entries

        # Get voting progress
        voting_progress = participant.voting_progress or {}

        # Save rankings
        voting_progress[f'question_{question_index}'] = rankings

        # If skipping, mark as absent
        if request.POST.get('is_skipping'):
            voting_progress[f'is_absent_q{question_index}'] = True
        else:
            # Clear any absence marker for this question
            absence_key = f'is_absent_q{question_index}'
            if absence_key in voting_progress:
                del voting_progress[absence_key]

        # Update current question
        voting_progress['current_question'] = question_index + 1
        SlotParticipant.objects.filter(id=participant_id).update(
            voting_progress=voting_progress
        )
        # Save progress to THIS specific participant record
        participant.voting_progress = voting_progress

        participant.save(update_fields=['voting_progress'])

        return JsonResponse({
            'status': 'success',
            'message': 'Rankings submitted successfully',
            'current_question': voting_progress.get('current_question', 1),
            'slot_id': slot.slot_id,
            'group_name': group_name
        })

    except Exception as e:
        # Log the full error for server-side debugging
        import traceback
        print(f"Error submitting rankings: {str(e)}")
        print(traceback.format_exc())

        return JsonResponse({
            'status': 'error',
            'message': f'Error submitting rankings: {str(e)}',
        }, status=500)

def get_room_status_response(slot, slot_group, participant, group_name):
    """
    Generate status update response for AJAX polling - strictly for this user/slot/group
    """
    # IMPORTANT: Get ONLY this participant's data - don't query other participants
    # This ensures we're only dealing with the specific user's status

    # Get this user's voting progress
    voting_progress = participant.voting_progress or {}
    current_question = int(voting_progress.get('current_question', 1))

    # Get the level for question count
    level = slot_group.level
    total_questions = 0

    # Count total questions
    for i in range(1, 13):
        question_field = f'question{i}'
        question_text = getattr(level, question_field, '')
        if question_text and question_text.strip():
            total_questions += 1
    total_questions = min(total_questions, 10)  # Limit to first 10 questions

    # Check if results have been published
    results_published = False
    if voting_progress and isinstance(voting_progress, dict):
        results_published = voting_progress.get('results_published') is True

    # Get only this participant's voting status - critical for UI state
    user_voting_status = participant.voting_status

    # Calculate parameters for UI
    max_ranks = determine_max_ranks(
        SlotParticipant.objects.filter(slot=slot, group_name=group_name).count()
    )

    # Only prepare ranked members if results are published
    ranked_members_json = []
    user_rank = 0
    user_mark = getattr(participant, 'mark', 0) or 0

    if results_published:
        # Get group members only when needed for results
        group_members = SlotParticipant.objects.filter(
            slot=slot,
            group_name=group_name
        ).select_related('user')

        # Sort members by mark (descending)
        ranked_members = sorted(
            group_members,
            key=lambda m: getattr(m, 'mark', 0) or 0,
            reverse=True
        )

        # Find current user's rank
        for idx, member in enumerate(ranked_members):
            if member.id == participant.id:
                user_rank = idx + 1
                break

        # Format for JSON response
        for idx, member in enumerate(ranked_members[:max_ranks]):
            ranked_members_json.append({
                'id': member.id,
                'name': member.user.name,
                'rank': idx + 1,
                'mark': getattr(member, 'mark', 0) or 0,
                'is_current_user': member.id == participant.id,
                'photo_url': member.user.photo.url if hasattr(member.user, 'photo') and member.user.photo else None
            })

    # Prepare basic response with this user's data ONLY
    response_data = {
        'status': 'success',
        'results_published': results_published,
        'current_question': current_question,
        'total_questions': total_questions,
        'voting_status': user_voting_status,
        'user_mark': user_mark,
        'user_rank': user_rank,
        'ranked_members': ranked_members_json,
        'request_voting_status': participant.request_voting,
        # Include identifiers to help client verify correct data
        'user_id': participant.user.id,
        'slot_id': slot.slot_id,
        'group_name': group_name
    }

    # Add redirect URL if results are published
    if results_published:
        from django.urls import reverse
        response_data['redirect_url'] = reverse('session_results',
                                                kwargs={'slot_id': slot.slot_id}) + f'?group={group_name}'

    return JsonResponse(response_data)


@login_required
def session_results(request, slot_id):
    """
    View function to display session results for a participant after results have been published.

    Parameters:
    request (HttpRequest): The HTTP request
    slot_id (str): The ID of the slot to display results for

    Returns:
    HttpResponse: The rendered results page
    """
    try:
        # Get the slot
        slot = get_object_or_404(Slot, slot_id=slot_id)

        # Check if a group was specified in query params
        group_name = request.GET.get('group')

        # If no group name provided, try to find a group for this user in this slot
        if not group_name:
            user_groups = SlotGroup.objects.filter(
                slot=slot,
                participants=request.user.userprofile
            )
            if user_groups.exists():
                group_name = user_groups.first().group_name
            else:
                message = 'Sorry, could not find your results. You are not assigned to any group in this slot.'
                return render(request, 'pages/error.html', {
                    'error_title': 'Results Not Found',
                    'error_message': message
                })

        # Get the SlotGroup and validate user's participation
        try:
            slot_group = SlotGroup.objects.get(
                slot=slot,
                group_name=group_name
            )

            # Check if user is part of this group
            if request.user.userprofile not in slot_group.participants.all():
                message = 'Sorry, could not access results. You are not a participant in this group.'
                return render(request, 'pages/error.html', {
                    'error_title': 'Access Denied',
                    'error_message': message
                })

            # Check if results have been published
            # Get the participant record
            participant = SlotParticipant.objects.get(
                slot=slot,
                group_name=group_name,
                user=request.user.userprofile
            )

            # Check if results have been published for this participant
            if not (participant.voting_progress and participant.voting_progress.get('results_published', False)):
                message = 'Results have not been published yet for this session.'
                return render(request, 'pages/error.html', {
                    'error_title': 'Results Not Available',
                    'error_message': message
                })

        except SlotGroup.DoesNotExist:
            message = 'Sorry, could not access results. Group not found.'
            return render(request, 'pages/error.html', {
                'error_title': 'Group Not Found',
                'error_message': message
            })

        except SlotParticipant.DoesNotExist:
            message = 'Sorry, could not access results. Your participant record was not found.'
            return render(request, 'pages/error.html', {
                'error_title': 'Participant Not Found',
                'error_message': message
            })

        # All validation passed, prepare data for the template

        # Get all participants in the group
        group_members = SlotParticipant.objects.filter(
            slot=slot,
            group_name=group_name
        ).select_related('user')

        # Calculate group parameters based on size
        group_size = group_members.count()
        max_ranks = determine_max_ranks(group_size)

        # Get ranked members sorted by mark
        ranked_members = sorted(
            group_members,
            key=lambda m: getattr(m, 'mark', 0) or 0,
            reverse=True
        )

        # Find current user's rank
        user_rank = 0
        for idx, member in enumerate(ranked_members):
            if member.id == participant.id:
                user_rank = idx + 1
                break

        # Get assigned topic
        assigned_topic = slot_group.topic

        # Prepare context for template
        context = {
            'slot': slot,
            'slot_group': slot_group,
            'participant': participant,
            'user_profile': request.user.userprofile,
            'ranked_members': ranked_members,
            'user_mark': getattr(participant, 'mark', 0) or 0,
            'user_rank': user_rank,
            'assigned_topic': assigned_topic,
            'voting_parameters': {
                'max_ranks': max_ranks,
            }
        }

        return render(request, 'pages/session_results.html', context)

    except Exception as e:
        import traceback
        print(f"Error displaying results: {str(e)}")
        print(traceback.format_exc())
        return render(request, 'pages/error.html', {
            'error_title': 'Error Displaying Results',
            'error_message': f'An error occurred while trying to display your results: {str(e)}'
        })



########################################################################################
################################################################################
##################### HOSTING PAGE AREA  #####################################
################################################################################
########################################################################################

@login_required
def join_group_from_qr(request):
    """
    View to handle joining a group from QR code scan

    Two-step process:
    1. Confirm - Get group details for confirmation (action='confirm')
    2. Join - Actually join the group after confirmation
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        }, status=405)

    try:
        # Get form data
        slot_id = request.POST.get('slot_id')
        group_name = request.POST.get('group_name')
        action = request.POST.get('action', '')  # 'confirm' or default join action

        # Check if we have both slot_id and group_name
        if not slot_id or not group_name:
            return JsonResponse({
                'status': 'error',
                'message': 'Slot ID and Group Name are required'
            }, status=400)

        # Get the current user's profile
        user_profile = request.user.userprofile

        # Find the slot
        try:
            slot = Slot.objects.get(slot_id=slot_id)
        except Slot.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid Slot ID'
            }, status=404)

        # Ensure the slot is live
        if slot.slot_status != 'live':
            return JsonResponse({
                'status': 'error',
                'message': 'This slot is not currently active'
            }, status=400)

        # Find the specific group within the slot
        try:
            slot_group = SlotGroup.objects.get(
                slot=slot,
                group_name=group_name
            )
        except SlotGroup.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid Group'
            }, status=404)

        # Check group status (start or pause)
        if slot_group.start_status not in ['start', 'pause']:
            return JsonResponse({
                'status': 'error',
                'message': 'This group is not currently available'
            }, status=400)

        # Check if user is already in the group
        if user_profile in slot_group.participants.all():
            return JsonResponse({
                'status': 'error',
                'message': 'You are already in this group'
            }, status=400)

        # Check if user has already completed this level
        has_already_completed = Achievements.objects.filter(
            user=request.user,
            event=slot_group.event,
            finished_level=slot_group.level
        ).exists()

        if has_already_completed:
            return JsonResponse({
                'status': 'error',
                'message': f'You have already completed Level {slot_group.level.level} - {slot_group.level.name} for this event'
            }, status=400)

        # NEW CODE: Check if this level requires prerequisites
        current_level = slot_group.level

        # If level number is greater than 1, check if user has completed previous levels
        if current_level.level > 1:
            # Check if the user has completed level 1 (or the immediate prerequisite level)
            previous_level_num = current_level.level - 1

            # Try to find the previous level for this event
            try:
                previous_level = Levels.objects.get(
                    event=slot_group.event,
                    level=previous_level_num
                )

                # Check if user has completed the previous level
                has_completed_previous = Achievements.objects.filter(
                    user=request.user,
                    event=slot_group.event,
                    finished_level=previous_level
                ).exists()

                if not has_completed_previous:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'You must complete Level {previous_level_num} - {previous_level.name} first'
                    }, status=400)

            except Levels.DoesNotExist:
                # If the previous level doesn't exist, then we'll check the specific prerequisite
                pass

            # If the level has a specific prerequisite defined, check that too
            if current_level.prerequisite:
                has_completed_prerequisite = Achievements.objects.filter(
                    user=request.user,
                    event=slot_group.event,
                    finished_level=current_level.prerequisite
                ).exists()

                if not has_completed_prerequisite:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'You must complete {current_level.prerequisite.name} (Level {current_level.prerequisite.level}) first'
                    }, status=400)

        # Prepare response details
        response_data = {
            'group': {
                'id': slot_group.id,
                'name': slot_group.group_name,
            },
            'slot': {
                'id': slot.slot_id,
                'event_name': slot_group.event.event_name,
                'level_number': slot_group.level.level,
                'level_name': slot_group.level.name,
                'date': slot_group.date.strftime('%d %b %Y') if hasattr(slot_group,
                                                                        'date') and slot_group.date else 'Date not available',
                'time': f"{slot_group.start_time.strftime('%I:%M %p')} - {slot_group.end_time.strftime('%I:%M %p') if slot_group.end_time else ''}" if hasattr(
                    slot_group, 'start_time') and slot_group.start_time else 'Time not available',
                'venue': slot.venue.venue_name if hasattr(slot, 'venue') and slot.venue else 'N/A'
            }
        }

        # If this is just a confirmation request, return group details without joining
        if action == 'confirm':
            # Include level completion and prerequisite info in the confirmation response
            if has_already_completed:
                response_data['level_completed'] = True
                response_data[
                    'warning_message'] = f'You have already completed Level {slot_group.level.level} - {slot_group.level.name} for this event'

            # Add warning about prerequisites if needed
            if current_level.level > 1:
                try:
                    previous_level = Levels.objects.get(
                        event=slot_group.event,
                        level=previous_level_num
                    )

                    has_completed_previous = Achievements.objects.filter(
                        user=request.user,
                        event=slot_group.event,
                        finished_level=previous_level
                    ).exists()

                    if not has_completed_previous:
                        response_data['missing_prerequisite'] = True
                        response_data[
                            'prerequisite_message'] = f'You must complete Level {previous_level_num} - {previous_level.name} first'
                except Levels.DoesNotExist:
                    pass

            return JsonResponse({
                'status': 'success',
                'message': 'Group details retrieved successfully',
                **response_data
            })

        # Check for existing active groups only if joining (not just confirming)
        active_groups = SlotGroup.objects.filter(
            Q(participants=user_profile) &  # User is in the group
            Q(slot__slot_status='live') &  # Slot is live
            Q(start_status__in=['start', 'pause'])  # Group is started or paused
        )

        if active_groups.exists():
            # User is already in an active group
            active_group = active_groups.first()
            return JsonResponse({
                'status': 'error',
                'message': f'You are already in an active group (Slot {active_group.slot.slot_id}, Group {active_group.group_name})'
            }, status=400)

        # If we get here, we're actually joining the group
        # Add user to the group's participants
        slot_group.participants.add(user_profile)

        # Create or update SlotParticipant entry
        slot_participant, created = SlotParticipant.objects.update_or_create(
            slot=slot,
            group_name=group_name,
            user=user_profile,
            defaults={
                'topic': slot_group.topic,
                'participant_status': 'on_going',
                'joined': False,
                'voting_status': 'not_started',
                'voting_progress': {},
                'finished_level': False
            }
        )

        # Return success response with redirect URL
        return JsonResponse({
            'status': 'success',
            'message': 'Successfully joined the group',
            **response_data,
            'redirect_url': reverse('my_slots_page')
        })

    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error joining group from QR: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }, status=500)

@login_required
def host_slots_page(request):
    # Check if user is superuser or belongs to faculty/slot host group
    is_superuser = request.user.is_superuser
    is_slot_creator = request.user.groups.filter(name='slot creator').exists()
    is_authorized = is_superuser or request.user.groups.filter(name__in=['slot host']).exists()

    if not is_authorized:
        messages.error(request, "You are not authorized to access this page.")
        return redirect('available_slots_page')

    # Get base queryset - different for superuser vs regular faculty
    if is_superuser:
        # Superuser sees all slots
        assigned_slots = Slot.objects.all().select_related('venue', 'created_by', 'assigned_to')
    else:
        # Regular faculty only sees slots assigned to them
        assigned_slots = Slot.objects.filter(
            assigned_to=request.user.userprofile
        ).select_related('venue')

    # Handle search parameter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        assigned_slots = assigned_slots.filter(
            Q(slot_id__icontains=search_query) |
            Q(created_by__name__icontains=search_query) |
            Q(assigned_to__name__icontains=search_query) |
            Q(venue__venue_name__icontains=search_query)
        )

    # Get all groups associated with these slots
    slot_ids = assigned_slots.values_list('id', flat=True)
    slot_groups = SlotGroup.objects.filter(
        slot__id__in=slot_ids
    ).select_related('slot')

    # Get participant counts per slot
    from django.db.models import Count
    participant_counts = SlotParticipant.objects.filter(
        slot__id__in=slot_ids
    ).values('slot_id').annotate(
        count=Count('id')
    )

    # Create a lookup dict for participant counts
    participant_count_dict = {p['slot_id']: p['count'] for p in participant_counts}

    # Prepare faculty slots for template
    faculty_slots = []
    for slot in assigned_slots:
        # Get groups for this slot
        groups = [group for group in slot_groups if group.slot_id == slot.id]

        # Add slot data to list
        slot_data = {
            'slot_id': slot.slot_id,
            'created_at': slot.created_at,
            'venue': slot.venue,
            'slot_status': slot.slot_status,
            'groups': groups,
            'groups_count': len(groups),
            'participants_count': participant_count_dict.get(slot.id, 0)
        }

        # Add created_by and assigned_to for superusers
        if is_superuser:
            slot_data.update({
                'created_by': slot.created_by,
                'assigned_to': slot.assigned_to
            })

        faculty_slots.append(slot_data)

    # Order by creation date (most recent first)
    faculty_slots = sorted(faculty_slots, key=lambda x: x['created_at'], reverse=True)

    # Get slot hosts (users in 'slot host' group)
    slot_hosts = UserProfile.objects.filter(user__groups__name='slot host')

    # Get venues and levels
    venues = Venue.objects.all()
    levels = Levels.objects.all()

    context = {
        'faculty_slots': faculty_slots,
        'is_superuser': is_superuser,
        'is_slot_creator': is_slot_creator,
        'slot_hosts': slot_hosts,
        'venues': venues,
        'levels': levels,
        'search_query': search_query  # Add this to keep the search term in the input
    }

    return render(request, 'pages/host_slots.html', context)


@login_required
def fetch_ended_groups(request, slot_id):
    """
    Fetch all ended groups with their participant details
    """
    try:
        # Get the slot
        slot = get_object_or_404(Slot, slot_id=slot_id)

        # Check authorization
        is_superuser = request.user.is_superuser
        is_assigned_faculty = hasattr(request.user, 'userprofile') and request.user.userprofile == slot.assigned_to
        is_authorized = is_superuser or is_assigned_faculty or request.user.groups.filter(
            name__in=['slot host', 'faculty']).exists()

        if not is_authorized:
            return JsonResponse({
                'status': 'error',
                'message': 'Not authorized to view ended groups'
            }, status=403)

        # Fetch ended groups - include both finished=True and start_status='end'
        ended_groups = SlotGroup.objects.filter(
            slot=slot
        ).filter(
            Q(finished=True) | Q(start_status='end')
        ).select_related('event', 'level', 'topic')

        # Prepare detailed group data
        ended_groups_data = []
        for group in ended_groups:
            # Fetch all participants for this group
            participants = SlotParticipant.objects.filter(
                slot=slot,
                group_name=group.group_name
            ).select_related('user', 'topic')

            # Prepare participant details
            participant_details = []
            for participant in participants:
                # Safely access attributes that might be None
                participant_details.append({
                    'name': participant.user.name,
                    'roll_number': getattr(participant.user, 'roll_number', None),
                    'staff_id': getattr(participant.user, 'staff_id', None),
                    'department': getattr(participant.user, 'department', None),
                    'mark': participant.mark,
                    'voting_status': participant.voting_status,
                    'participant_status': participant.participant_status,
                    'joined': participant.joined,
                    # Only include essential voting progress data, not the entire object
                    'voting_progress': {
                        'current_question': participant.voting_progress.get('current_question',
                                                                            1) if participant.voting_progress else 1,
                        'results_published': participant.voting_progress.get('results_published',
                                                                             False) if participant.voting_progress else False
                    }
                })

            # Sort participants by mark in descending order
            participant_details.sort(key=lambda x: x['mark'] or 0, reverse=True)

            # Extract analytics report filename from group metadata
            analytics_report = None
            if hasattr(group, 'metadata') and group.metadata:
                # Check if metadata is a string (possible JSON string)
                if isinstance(group.metadata, str):
                    try:
                        import json
                        metadata_dict = json.loads(group.metadata)
                        analytics_report = metadata_dict.get('analytics_report')
                    except (json.JSONDecodeError, ValueError, TypeError):
                        print(f"Error parsing metadata string for group {group.id}")
                        analytics_report = None
                else:
                    # Metadata is already a dictionary
                    analytics_report = group.metadata.get('analytics_report')

            # Debug output to help troubleshoot
            print(f"Group {group.group_name} metadata: {group.metadata}")
            print(f"Analytics report for group {group.group_name}: {analytics_report}")

            # Prepare group data
            group_data = {
                'id': group.id,
                'group_name': group.group_name,
                'event_name': group.event.event_name,
                'level_name': group.level.name,
                'level_number': group.level.level,
                'topic': group.topic.topic_name if group.topic else None,
                'date': group.date.strftime('%Y-%m-%d'),
                'start_time': group.start_time.strftime('%H:%M'),
                'end_time': group.end_time.strftime('%H:%M') if group.end_time else None,
                'start_status': group.start_status,
                'finished': group.finished,
                'total_participants': len(participant_details),
                'participants': participant_details,
                'analytics_report': analytics_report,
                'metadata': group.metadata  # Include the full metadata for additional flexibility
            }

            ended_groups_data.append(group_data)

        return JsonResponse({
            'status': 'success',
            'ended_groups': ended_groups_data
        })

    except Exception as e:
        import traceback
        print(f"Error fetching ended groups: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while fetching ended groups'
        }, status=500)

def publish_results(request, group_id):
    """
    Handler for publishing results for a specific group.
    Now also generates an analytics report and saves the path in the group metadata.

    This function:
    1. Validates permissions (only slot hosts or admins can publish)
    2. Gets all participants in the group
    3. Calculates final marks for all questions
    4. Generates an analytics report
    5. Updates group state and creates achievements
    6. Returns appropriate response

    Parameters:
    request (HttpRequest): The HTTP request
    group_id (int): ID of the group to publish results for

    Returns:
    JsonResponse: Response with status and message
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        # Get the slot group
        group_id = request.POST.get('group_id')
        if not group_id:
            return JsonResponse({'status': 'error', 'message': 'Group ID is required'}, status=400)

        # Get the group
        group = get_object_or_404(SlotGroup, id=group_id)

        # Verify the user has permission to publish results
        if not request.user.is_superuser and request.user.userprofile != group.slot.assigned_to:
            return JsonResponse({
                'status': 'error',
                'message': 'You do not have permission to publish results for this group'
            }, status=403)

        # Get all participants in the group
        participants = SlotParticipant.objects.filter(
            slot=group.slot,
            group_name=group.group_name
        ).select_related('user')

        if not participants.exists():
            return JsonResponse({'status': 'error', 'message': 'No participants found in this group'}, status=404)

        # First determine how many questions need to be processed
        question_count = 0
        level = group.level
        for i in range(1, 13):  # question1 through question12
            question_field = f'question{i}'
            question_text = getattr(level, question_field, '')
            if question_text and question_text.strip():
                question_count += 1

        # Limit to first 10 questions
        question_count = min(question_count, 10)

        # Make sure all individual questions have been calculated first
        for q_num in range(1, question_count + 1):
            print(f"Ensuring marks calculated for question {q_num}")
            calculate_marks_for_question(group, list(participants), q_num)

        # Now calculate the final results (passing None as question_number)
        # This will also generate the analytics report
        success = calculate_marks_for_question(group, list(participants), None)

        if not success:
            return JsonResponse({
                'status': 'error',
                'message': 'Error occurred while calculating final results'
            }, status=500)

        # Get report path from group metadata
        report_filename = None
        if hasattr(group, 'metadata') and group.metadata:
            report_filename = group.metadata.get('analytics_report')

        # If report wasn't generated in calculate_marks_for_question, generate it now
        if not report_filename:
            try:
                report_filename = generate_group_analytics_report(group, list(participants))

                # Save the report filename to the group's metadata
                metadata = group.metadata or {}
                metadata['analytics_report'] = report_filename
                group.metadata = metadata
                group.save(update_fields=['metadata'])

                print(f"Analytics report generated: {report_filename}")
            except Exception as report_error:
                print(f"Error generating report: {str(report_error)}")
                import traceback
                print(traceback.format_exc())
                # Continue with the publishing process even if report generation failed

        # Sort participants by mark to get rankings
        ranked_participants = sorted(participants, key=lambda p: p.mark or 0, reverse=True)

        # Determine max ranks based on group size
        group_size = participants.count()
        max_ranks = determine_max_ranks(group_size)

        # Set results_published flag and update participant status
        for participant in participants:
            # Make a fresh query to get the latest data for this participant
            latest_participant = SlotParticipant.objects.get(id=participant.id)

            # Get the current voting progress with fallback to empty dict
            voting_progress = copy.deepcopy(latest_participant.voting_progress) or {}

            # Add the results_published flag (don't replace the entire dict)
            voting_progress['results_published'] = True

            # Update the participant object
            latest_participant.voting_progress = voting_progress
            latest_participant.voting_status = 'finished'
            latest_participant.participant_status = 'completed'

            # Save with explicit update_fields to prevent unexpected changes
            latest_participant.save(update_fields=['voting_progress', 'voting_status', 'participant_status'])

            # Find participant's rank to check if they placed within max_ranks
            current_rank = None
            for idx, ranked_p in enumerate(ranked_participants):
                if ranked_p.id == participant.id:
                    current_rank = idx + 1
                    break

            # Only create achievement if the participant placed within the max ranks
            if current_rank is not None and current_rank <= max_ranks:
                # Create or update achievement record - only save mark, not rank
                achievement, created = Achievements.objects.update_or_create(
                    user=participant.user.user,  # Assuming user is a UserProfile
                    finished_level=group.level,
                    slot_id=group.slot.slot_id,
                    group_name=group.group_name,
                    defaults={
                        'mark': participant.mark,
                        'event': group.event
                    }
                )



        # Remove all participants from the M2M relationship while keeping SlotParticipant records

        group.start_status = 'end'
        group.finished = True
        group.save(update_fields=['start_status','finished'])

        # Add report path to response if available
        response_data = {
            'status': 'success',
            'message': f"Results for group {group.group_name} published successfully!"
        }

        if report_filename:
            response_data['report_filename'] = report_filename
            response_data['report_url'] = f"/download_report/{report_filename}/"



        # Return success response
        return JsonResponse(response_data)

    except Exception as e:
        import traceback
        print(f"Error publishing results: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



@login_required
def host_slot_detail(request, slot_id):
    # Get the slot
    slot = get_object_or_404(Slot, slot_id=slot_id)

    # Check if the current user is the assigned faculty
    if request.user.userprofile != slot.assigned_to:
        messages.error(request, "You are not authorized to host this slot.")
        return redirect('host_slots_page')

    # Get slot groups with all related objects
    slot_groups = SlotGroup.objects.filter(slot=slot).select_related('event', 'level', 'topic')

    # Get all events, levels, topics for dropdowns
    all_events = Event.objects.filter(status='active')
    all_levels = Levels.objects.filter(status='active').select_related('event')
    all_topics = Topic.objects.filter(status='active').select_related('level')
    all_participants = SlotParticipant.objects.filter(slot=slot).select_related('user')

    # Prepare groups data
    groups_list = []
    all_groups_completed = True
    all_results_published = True


    for slot_group in slot_groups:
        # Get all participants in this group
        participants = SlotParticipant.objects.filter(
            slot=slot,
            group_name=slot_group.group_name
        ).select_related('user')

        # Calculate group statistics
        filled_capacity = participants.count()

        # Calculate participant status
        joined_count = participants.filter(joined=True).count()
        voting_count = participants.filter(voting_status='in_progress').count()

        # Count participants who might have requested voting
        requested_count = sum(
            1 for p in participants
            if p.voting_progress and p.voting_progress.get('request_voting') == 'request'
        )

        completed_count = participants.filter(voting_status='finished').count()

        # Determine group voting status
        all_participants_completed = all(
            p.voting_status == 'finished' for p in participants
        )

        group_has_results_published = all(
            p.voting_progress.get('results_published', False)
            if hasattr(p, 'voting_progress') and p.voting_progress
            else False
            for p in participants
        )

        # Ranked members based on marks
        group_ranked_members = sorted(
            participants,
            key=lambda m: getattr(m, 'mark', 0) or 0,
            reverse=True
        )


        # Prepare group info - include the actual SlotGroup object for direct access
        group_info = {
            'id': slot_group.id,
            'group_name': slot_group.group_name,
            'event': slot_group.event,
            'level': slot_group.level,
            'topic': slot_group.topic,
            'date': slot_group.date,
            'start_time': slot_group.start_time,
            'end_time': slot_group.end_time,
            'start_status': slot_group.start_status,
            'filled_capacity': filled_capacity,
            'joined_count': joined_count,
            'voting_count': voting_count,
            'requested_count': requested_count,
            'completed_count': completed_count,
            'all_voting_in_progress': all(p.voting_status == 'in_progress' for p in participants),
            'voting_status_display': (
                "not_started" if filled_capacity == 0 else
                "completed" if all_participants_completed else
                "in_progress"
            ),

            'results_published': group_has_results_published,
            'ranked_members': group_ranked_members,
            'requested_voting_count': requested_count,
            'all_requested_voting': requested_count == len(participants) and len(participants) > 0,
        }

        if slot.slot_status == 'live'   and not slot_group.finished:
                groups_list.append(group_info)
        elif slot.slot_status == 'expired'  and not slot_group.finished:
            groups_list.append(group_info)

        # Update overall completion flags
        if not all_participants_completed:
            all_groups_completed = False

        if not group_has_results_published:
            all_results_published = False

    # When preparing participant data in host_slot_detail view
    for participant in all_participants:
        # Add a check to mark participants as finished if they've completed all questions
        if participant.voting_status == 'in_progress' and participant.voting_progress:
            # Get level to determine total questions
            group_obj = next((g for g in slot_groups if g.group_name == participant.group_name), None)
            if group_obj and group_obj.level:
                total_questions = 0
                for i in range(1, 13):  # question1 through question12
                    question_field = f'question{i}'
                    question_text = getattr(group_obj.level, question_field, '')
                    if question_text and question_text.strip():
                        total_questions += 1

                # Store total questions on the participant for template use
                participant.actual_total_questions = total_questions

                current_question = participant.voting_progress.get('current_question', 1)

                # If current_question is greater than total_questions, mark as finished
                if current_question > total_questions and participant.voting_status != 'finished':
                    participant.voting_status = 'finished'

                    # Update the voting_progress to reflect completed status
                    if participant.voting_progress:
                        participant.voting_progress['completed'] = True
                        # IMPORTANT: Do NOT add 'results_published' = True here

                    participant.save()

    # Calculate slot capacity statistics
    total_participants = SlotParticipant.objects.filter(slot=slot).count()
    joined_participants = SlotParticipant.objects.filter(slot=slot, joined=True).count()

    # Prepare context
    context = {
        'slot': slot,
        'groups_list': groups_list,
        'slot_groups': slot_groups,
        'total_participants': total_participants,
        'joined_participants': joined_participants,
        'all_groups_completed': all_groups_completed,
        'results_published': all_results_published,
        'all_events': all_events,
        'all_levels': all_levels,
        'all_topics': all_topics,
        'all_participants': all_participants,
        'today_date': datetime.today(),
    }

    # Handle POST requests
    if request.method == 'POST':
        action = request.POST.get('action')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Helper function to create response based on request type
        def create_response(status, message, redirect_url=None, data=None):
            if is_ajax:
                response_data = {
                    'status': status,
                    'message': message
                }
                if data:
                    response_data.update(data)
                return JsonResponse(response_data)
            else:
                if status == 'success':
                    messages.success(request, message)
                else:
                    messages.error(request, message)
                return redirect(redirect_url or 'host_slot_detail', slot_id=slot.slot_id)

        if action == 'toggle_slot_status':
            # Toggle slot status between 'live' and 'expired'
            try:
                current_status = slot.slot_status
                new_status = 'expired' if current_status == 'live' else 'live'

                slot.slot_status = new_status

                slot.save()

                # Update all associated groups' status
                SlotGroup.objects.filter(slot=slot).update(start_status=new_status)

                return create_response('success', f"Slot status updated to {new_status}")

            except Exception as e:
                return create_response('error', f"Error updating slot status: {str(e)}")

        elif action == 'edit_group':
            # Edit existing group
            try:
                group_id = request.POST.get('group_id')
                group = SlotGroup.objects.get(id=group_id, slot=slot)

                # Only update details if group is not in 'start' status
                if group.start_status != 'start':
                    # Get form data
                    event_id = request.POST.get('event')
                    level_id = request.POST.get('level')
                    topic_id = request.POST.get('topic')
                    date_str = request.POST.get('date')
                    start_time_str = request.POST.get('start_time')
                    end_time_str = request.POST.get('end_time')

                    # Update event if provided
                    if event_id:
                        group.event = get_object_or_404(Event, id=event_id)

                    # Update level if provided
                    if level_id:
                        group.level = get_object_or_404(Levels, id=level_id)

                    # Update topic if provided
                    if topic_id:
                        group.topic = get_object_or_404(Topic, id=topic_id)
                    elif topic_id == '':  # Handle case when "Random Topic" is selected
                        # Get a random topic for this level if available
                        if group.level:
                            topics = Topic.objects.filter(level=group.level, status='active')
                            topics_list = list(topics)
                            import random
                            if topics_list:
                                group.topic = random.choice(topics_list)
                            else:
                                group.topic = None

                    # Update date
                    if date_str:
                        group.date = datetime.strptime(date_str, '%Y-%m-%d').date()

                    # Update start time
                    if start_time_str:
                        group.start_time = datetime.strptime(start_time_str, '%H:%M').time()

                    # Update end time
                    if end_time_str:
                        group.end_time = datetime.strptime(end_time_str, '%H:%M').time()
                    elif group.start_time and group.level and group.level.total_duration:
                        # Calculate end time based on start time and level duration
                        start_datetime = datetime.combine(group.date, group.start_time)
                        end_datetime = start_datetime + timedelta(minutes=group.level.total_duration)
                        group.end_time = end_datetime.time()

                # Save the updated group
                group.save()

                return create_response('success', f"Group {group.group_name} updated successfully!")

            except Exception as e:
                return create_response('error', f"Error updating group: {str(e)}")

        elif action == 'remove_participant':
            # Remove participant from group
            try:
                participant_id = request.POST.get('participant_id')
                group_id = request.POST.get('group_id')

                # Get objects
                participant = get_object_or_404(SlotParticipant, id=participant_id)
                group = get_object_or_404(SlotGroup, id=group_id)

                # Check if removal is allowed
                if group.start_status == 'start' and participant.voting_status == 'in_progress':
                    return create_response('error', "Cannot remove participant during active voting session")

                # Remove user from SlotGroup's participants
                if participant.user in group.participants.all():
                    group.participants.remove(participant.user)

                # Delete the SlotParticipant entry
                participant.delete()

                return create_response('success', "Participant removed successfully")

            except Exception as e:
                return create_response('error', f"Error removing participant: {str(e)}")


        # Add this to your existing host_slot_detail view function where the other POST actions are handled
        elif action == 'reset_group':
            # Reset group
            try:
                group_id = request.POST.get('group_id')
                group = SlotGroup.objects.get(id=group_id, slot=slot)

                # Remove all participants from the group
                SlotParticipant.objects.filter(
                    slot=slot,
                    group_name=group.group_name
                ).delete()

                # Remove all users from the M2M relationship
                #group.participants.clear()
                # Set group status to end
                group.start_status = 'end'
                group.save()

                return create_response('success', f"Group {group.group_name} has been reset successfully!")

            except Exception as e:
                return create_response('error', f"Error resetting group: {str(e)}")


        elif action == 'delete_group':
            # Delete group
            try:
                group_id = request.POST.get('group_id')
                group = SlotGroup.objects.get(id=group_id, slot=slot)

                # Check if deletion is allowed
                if group.start_status == 'start':
                    return create_response('error', "Cannot delete a group that is currently started")

                # Store group name for success message
                group_name = group.group_name

                # First delete all participants in this group
                SlotParticipant.objects.filter(
                    slot=slot,
                    group_name=group_name
                ).delete()

                # Then delete the group itself
                group.delete()

                return create_response('success', f"Group {group_name} deleted successfully!")

            except Exception as e:
                return create_response('error', f"Error deleting group: {str(e)}")

        elif action == 'add_group':
            # Create a new group
            try:
                # Get form data
                group_name = request.POST.get('group_name', '').strip() or None
                # Generate group name if not provided
                if not group_name:
                    # Count existing groups for this slot
                    existing_count = SlotGroup.objects.filter(slot=slot).count()

                    # Generate a random 2-3 digit number
                    import random
                    number = random.randint(10, 999)

                    # Get alphabet (A-Z) based on cycling through 26 letters
                    letter = chr(65 + (existing_count % 26))  # 65 is ASCII for 'A'

                    # Create group name like A34, B567, etc.
                    group_name = f"{letter}{number}"

                event_id = request.POST.get('event')
                level_id = request.POST.get('level')
                date_str = request.POST.get('date')
                start_time_str = request.POST.get('start_time')

                # Convert date string to date object
                date = datetime.strptime(date_str, '%Y-%m-%d').date()

                # Convert time string to time object
                start_time = datetime.strptime(start_time_str, '%H:%M').time()

                # Get event and level objects
                event = get_object_or_404(Event, id=event_id)
                level = get_object_or_404(Levels, id=level_id)

                # Calculate end time based on level duration
                start_datetime = datetime.combine(date, start_time)
                end_datetime = start_datetime + timedelta(minutes=level.total_duration)
                end_time = end_datetime.time()

                # Get a random topic for this event and level
                topics = Topic.objects.filter(level=level, status='active')
                topic = None
                if topics.exists():
                    # Get a random topic from the queryset
                    topics_list = list(topics)
                    if topics_list:
                        topic = random.choice(topics_list)

                # Create the group
                new_group = SlotGroup.objects.create(
                    slot=slot,
                    group_name=group_name,
                    event=event,
                    level=level,
                    topic=topic,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    start_status='pause'  # Always start with paused status
                )

                return create_response('success', f"Group {new_group.group_name} created successfully!")
            except Exception as e:
                return create_response('error', f"Error creating group: {str(e)}")

        elif action == 'update_start_status':
            # Update group start status
            try:
                group_id = request.POST.get('group_id')
                start_status = request.POST.get('start_status')
                group = SlotGroup.objects.get(id=group_id, slot=slot)
                group.start_status = start_status  # Only changing group status, not participant join status
                group.save()
                return create_response('success', f"Group {group.group_name} status updated to {start_status}")

            except Exception as e:
                return create_response('error', f"Error updating group status: {str(e)}")


        elif action == 'pause_voting':
            # Pause voting for a group
            try:
                group_id = request.POST.get('group_id')
                group = SlotGroup.objects.get(id=group_id, slot=slot)

                # Get all participants in this group
                all_participants = SlotParticipant.objects.filter(
                    slot=slot,
                    group_name=group.group_name
                )


                # Important: Make sure to only update participants that are currently in progress
                # Do NOT use bulk update here as it may not work as expected
                updated_count = 0
                for participant in all_participants:
                    if participant.voting_status == 'in_progress':

                        participant.voting_status = 'not_started'
                        participant.save()
                        updated_count += 1


                # Always return success to ensure UI updates properly
                if updated_count > 0:
                    return create_response('success',
                                           f"Voting paused for {updated_count} participants in group {group.group_name}")
                else:
                    return create_response('success',
                                           f"No participants were in voting progress in group {group.group_name}")

            except Exception as e:
                import traceback
                print(traceback.format_exc())
                return create_response('error', f"Error pausing voting: {str(e)}")


        elif action == 'start_voting':
            # Start voting for a group
            try:
                group_id = request.POST.get('group_id')
                group = SlotGroup.objects.get(id=group_id, slot=slot)

                # Get all participants in this group regardless of status
                all_participants = SlotParticipant.objects.filter(
                    slot=slot,
                    group_name=group.group_name
                )

                # Update only non-finished participants to in_progress
                updated_count = 0
                for participant in all_participants:
                    if participant.voting_status != 'finished':
                        participant.voting_status = 'in_progress'
                        participant.save()
                        updated_count += 1
                return create_response('success', f"Voting started for group {group.group_name}")
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                return create_response('error', f"Error starting voting: {str(e)}")

        elif action == 'publish_results':
            # For publishing results, we'll use our dedicated function

            return publish_results(request, request.POST.get('group_id'))


    # Check if this is an AJAX request for HTML fragment
    if request.headers.get('X-Requested-With') == 'HtmlOnly':
        return render(request, 'pages/host_slot_detail.html', context)

    return render(request, 'pages/host_slot_detail.html', context)





# API view to get levels for a specific event
@login_required
def get_levels_for_event(request, event_id):
    try:
        # Fix: Make sure we're getting levels for this specific event
        event = get_object_or_404(Event, id=event_id)
        levels = Levels.objects.filter(event=event, status='active')

        # Format levels data for JSON response
        levels_data = [
            {
                'id': level.id,
                'name': level.name,
                'level': level.level,
                'total_duration': level.total_duration
            }
            for level in levels
        ]

        return JsonResponse({'levels': levels_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def group_updates(request, slot_id):
    """API endpoint to provide updates on groups and participants."""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'AJAX request required'}, status=400)

    # Get the slot
    slot = get_object_or_404(Slot, slot_id=slot_id)

    # Check if the current user is the assigned faculty
    if request.user.userprofile != slot.assigned_to:
        return JsonResponse({'status': 'error', 'message': 'Not authorized'}, status=403)

    # Get slot groups
    slot_groups = SlotGroup.objects.filter(slot=slot).select_related('event', 'level', 'topic')

    # Prepare groups data
    groups_data = []

    for group in slot_groups:
        # Get all participants in this group
        participants = SlotParticipant.objects.filter(
            slot=slot,
            group_name=group.group_name
        ).select_related('user')

        # Update participant statuses if needed
        for p in participants:
            # Calculate actual total questions
            group_level = group.level
            total_questions = 0
            if group_level:
                for i in range(1, 13):
                    question_field = f'question{i}'
                    question_text = getattr(group_level, question_field, '')
                    if question_text and question_text.strip():
                        total_questions += 1

            # Check if participant has completed all questions
            if p.voting_status == 'in_progress' and p.voting_progress:
                current_question = p.voting_progress.get('current_question', 1)
                if current_question > total_questions:
                    p.voting_status = 'finished'
                    p.save()

        # Calculate group statistics
        filled_capacity = participants.count()
        joined_count = sum(1 for p in participants if p.joined)
        voting_count = sum(1 for p in participants if p.voting_status == 'in_progress')
        completed_count = sum(1 for p in participants if p.voting_status == 'finished')

        # Check if all participants have completed
        all_participants_completed = (completed_count == filled_capacity and filled_capacity > 0)

        # Count active voting requests
        requested_count = sum(
            1 for p in participants
            if p.voting_progress and p.voting_progress.get('request_voting') == 'request'
        )

        # Prepare participant data
        participants_data = []
        for p in participants:
            # Calculate details for this participant
            current_question = 0
            if p.voting_progress:
                current_question = p.voting_progress.get('current_question', 1)
                # Adjust for display
                if current_question > total_questions:
                    current_question = total_questions
                else:
                    current_question = max(0, current_question - 1)

            # Add participant info
            participants_data.append({
                'id': p.id,
                'name': p.user.name,
                'id_number': p.user.roll_number or p.user.staff_id,
                'photo': p.user.photo.url if p.user.photo else None,
                'joined': p.joined,
                'voting_status': p.voting_status,
                'request_voting': p.voting_progress.get('request_voting') if p.voting_progress else None,
                'current_question': current_question,
                'total_questions': total_questions
            })

        # Check if results have been published
        results_published = all(
            p.voting_progress and p.voting_progress.get('results_published', False)
            for p in participants
        ) if participants.exists() else False



        # Add group data
        groups_data.append({
            'id': group.id,
            'group_name': group.group_name,
            'event_id': group.event.id,
            'level_id': group.level.id,
            'topic_id': group.topic.id if group.topic else None,
            'start_status': group.start_status,
            'filled_capacity': filled_capacity,
            'joined_count': joined_count,
            'voting_count': voting_count,
            'completed_count': completed_count,
            'requested_count': requested_count,
            'participants': participants_data,
            'all_participants_completed': all_participants_completed,
            'results_published': results_published
        })

    return JsonResponse({
        'status': 'success',
        'timestamp': int(datetime.now().timestamp() * 1000),
        'groups': groups_data
    })

@login_required
def create_slot(request):
    # Check if user is superuser or in slot creator group
    is_authorized = request.user.is_superuser or request.user.groups.filter(name='slot creator').exists()

    if not is_authorized:
        messages.error(request, "You are not authorized to create slots.")
        return redirect('host_slots_page')

    if request.method == 'POST':
        try:
            # Get form data
            venue_id = request.POST.get('venue')

            # Validate inputs
            if not venue_id:
                messages.error(request, "Please select a venue.")
                return redirect('host_slots_page')

            # Get venue
            venue = Venue.objects.get(id=venue_id)

            # For superuser, check if assigned_to is provided
            assigned_to = None
            if request.user.is_superuser:
                assigned_to_id = request.POST.get('assigned_to')
                if assigned_to_id:
                    assigned_to = UserProfile.objects.get(id=assigned_to_id)

            # Create slot
            slot = Slot.objects.create(
                venue=venue,
                created_by=request.user.userprofile,
                assigned_to=assigned_to or request.user.userprofile,
                slot_status='live'
            )

            messages.success(request, f"Slot {slot.slot_id} created successfully!")
            return redirect('host_slots_page')

        except Exception as e:
            messages.error(request, f"Error creating slot: {str(e)}")
            return redirect('host_slots_page')

    return redirect('host_slots_page')


########################################################################################
################################################################################
##################### QUICK SLOT PAGE AREA  #####################################
################################################################################
########################################################################################http://127.0.0.1:8002/accounts/register/


