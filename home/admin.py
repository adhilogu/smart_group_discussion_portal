import hashlib

from django.contrib import admin
from django.apps import apps
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.urls import path
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.http import urlencode
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from rangefilter.filters import DateRangeFilter

from .models import *
from datetime import datetime, timedelta

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_number','mail_id','user_type' ,'display_photo', 'department', 'batch', 'phone_number',
                     'status_display', 'status_toggle', 'created_at')
    list_filter = (('created_at', DateRangeFilter),'status', 'department', 'batch')
    search_fields = ('name', 'roll_number', 'mail_id', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')

    def display_photo(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" />', obj.photo.url)
        return "No photo"

    display_photo.short_description = 'Profile Photo'

    def status_display(self, obj):
        if obj.status == 'active':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Inactive</span>'
        )

    status_display.short_description = 'Status'

    def status_toggle(self, obj):
        return format_html(
            '''
            <div style="width: 32px; height: 16px; background-color: {}; border-radius: 8px; position: relative; cursor: pointer;">
                <a href="{}?id={}" style="display: block; width: 100%; height: 100%; text-decoration: none;">
                    <span style="width: 12px; height: 12px; background-color: white; border-radius: 50%; position: absolute; top: 2px; {}"></span>
                </a>
            </div>
            ''',
            '#28a745' if obj.status == 'active' else '#dc3545',
            reverse('admin:toggle-user-status'),
            obj.id,
            'right: 2px;' if obj.status == 'active' else 'left: 2px;'
        )

    status_toggle.short_description = 'Toggle'

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'roll_number', 'department', 'batch','gender')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'mail_id')
        }),
        ('Profile', {
            'fields': ('photo', 'status','user_type','staff_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('toggle-user-status/',
                 self.admin_site.admin_view(self.toggle_user_status),
                 name='toggle-user-status'),
        ]
        return custom_urls + urls

    def toggle_user_status(self, request):
        user_id = request.GET.get('id')
        try:
            profile = UserProfile.objects.get(id=user_id)
            # Toggle the status
            new_status = 'inactive' if profile.status == 'active' else 'active'
            profile.status = new_status
            profile.user.is_active = new_status == 'active'
            profile.user.save()
            profile.save()
        except UserProfile.DoesNotExist:
            messages.error(request, 'User profile not found')

        # Add this return statement
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    def save_model(self, request, obj, form, change):
        # First save the UserProfile object
        super().save_model(request, obj, form, change)

        # Now update the User model
        user = obj.user
        user.email = obj.mail_id  # Sync email (using mail_id instead of email_id)
        user.first_name = obj.name  # Sync first name (using name instead of first_name)
        user.is_active = obj.status == 'active'  # Keep sync of active status
        user.save()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Double-check the synchronization after all related objects are saved
        obj = form.instance
        if obj.user.email != obj.mail_id:  # Using mail_id instead of email_id
            obj.user.email = obj.mail_id
            obj.user.first_name = obj.name
            obj.user.save()

        form.instance.save()  # Re-save to update any related fields


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_name','display_photo', 'status_display', 'status_toggle', 'created_at')
    search_fields = ('event_name',)
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

    def status_display(self, obj):
        if obj.status == 'active':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Inactive</span>'
        )

    status_display.short_description = 'Status'

    def status_toggle(self, obj):
        return format_html(
            '''
            <div style="width: 32px; height: 16px; background-color: {}; border-radius: 8px; position: relative; cursor: pointer;">
                <a href="{}?id={}" style="display: block; width: 100%; height: 100%; text-decoration: none;">
                    <span style="width: 12px; height: 12px; background-color: white; border-radius: 50%; position: absolute; top: 2px; {}"></span>
                </a>
            </div>
            ''',
            '#28a745' if obj.status == 'active' else '#dc3545',
            reverse('admin:toggle-event-status'),
            obj.id,
            'right: 2px;' if obj.status == 'active' else 'left: 2px;'
        )

    status_toggle.short_description = 'Toggle'

    fieldsets = (
        ('Event Information', {
            'fields': ('event_name', 'event_photo', 'status','eligible_groups')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_photo(self, obj):
        if obj.event_photo:
            return format_html('<img src="{}" width="50" height="50" />', obj.event_photo.url)
        return "No photo"

    display_photo.short_description = 'Event Photo'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('toggle-event-status/',
                 self.admin_site.admin_view(self.toggle_event_status),
                 name='toggle-event-status'),
        ]
        return custom_urls + urls

    def toggle_event_status(self, request):
        event_id = request.GET.get('id')
        try:
            event = Event.objects.get(id=event_id)
            new_status = 'inactive' if event.status == 'active' else 'active'
            event.status = new_status
            event.save()
        except Event.DoesNotExist:
            messages.error(request, 'Event not found')

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))






@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('venue_name', 'venue_capacity', 'status_display', 'status_toggle')
    search_fields = ('venue_name',)
    list_filter = ('status',)
    readonly_fields = ('created_at', 'updated_at')

    def status_display(self, obj):
        if obj.status == 'active':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Inactive</span>'
        )
    status_display.short_description = 'Status'

    def status_toggle(self, obj):
        return format_html(
            '''
            <div style="width: 32px; height: 16px; background-color: {}; border-radius: 8px; position: relative; cursor: pointer;">
                <a href="{}?id={}" style="display: block; width: 100%; height: 100%; text-decoration: none;">
                    <span style="width: 12px; height: 12px; background-color: white; border-radius: 50%; position: absolute; top: 2px; {}"></span>
                </a>
            </div>
            ''',
            '#28a745' if obj.status == 'active' else '#dc3545',
            reverse('admin:toggle-venue-status'),
            obj.id,
            'right: 2px;' if obj.status == 'active' else 'left: 2px;'
        )
    status_toggle.short_description = 'Toggle'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('toggle-venue-status/',
                 self.admin_site.admin_view(self.toggle_venue_status),
                 name='toggle-venue-status'),
        ]
        return custom_urls + urls

    def toggle_venue_status(self, request):
        venue_id = request.GET.get('id')
        try:
            venue = Venue.objects.get(id=venue_id)
            new_status = 'inactive' if venue.status == 'active' else 'active'
            venue.status = new_status
            venue.save()
        except Venue.DoesNotExist:
            messages.error(request, 'Venue not found')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@admin.register(Levels)
class LevelsAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'level', 'total_duration', 'prerequisite', 'status_display', 'status_toggle')
    search_fields = ('name', 'event__event_name')
    list_filter = ('status', 'event', 'level')
    readonly_fields = ('created_at', 'updated_at')

    def status_display(self, obj):
        if obj.status == 'active':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Inactive</span>'
        )
    status_display.short_description = 'Status'

    def status_toggle(self, obj):
        return format_html(
            '''
            <div style="width: 32px; height: 16px; background-color: {}; border-radius: 8px; position: relative; cursor: pointer;">
                <a href="{}?id={}" style="display: block; width: 100%; height: 100%; text-decoration: none;">
                    <span style="width: 12px; height: 12px; background-color: white; border-radius: 50%; position: absolute; top: 2px; {}"></span>
                </a>
            </div>
            ''',
            '#28a745' if obj.status == 'active' else '#dc3545',
            reverse('admin:toggle-level-status'),
            obj.id,
            'right: 2px;' if obj.status == 'active' else 'left: 2px;'
        )
    status_toggle.short_description = 'Toggle'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('toggle-level-status/',
                 self.admin_site.admin_view(self.toggle_level_status),
                 name='toggle-level-status'),
        ]
        return custom_urls + urls

    def toggle_level_status(self, request):
        level_id = request.GET.get('id')
        try:
            level = Levels.objects.get(id=level_id)
            new_status = 'inactive' if level.status == 'active' else 'active'
            level.status = new_status
            level.save()
        except Levels.DoesNotExist:
            messages.error(request, 'Level not found')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    fieldsets = (
        ('Basic Information', {
            'fields': ('event', 'level', 'name', 'total_duration', 'status')
        }),

        ('Agenda Details', {
            'fields': (
                ('agenda1_name', 'agenda1_duration'),
                ('agenda2_name', 'agenda2_duration'),
                ('agenda3_name', 'agenda3_duration'),
                ('agenda4_name', 'agenda4_duration'),
                ('agenda5_name', 'agenda5_duration'),
                ('agenda6_name', 'agenda6_duration'),
                ('agenda7_name', 'agenda7_duration'),
                ('agenda8_name', 'agenda8_duration'),
                ('agenda9_name', 'agenda9_duration'),
                ('agenda10_name', 'agenda10_duration'),
            )
        }),

        ('Questions', {
            'fields': (
                'question1',
                'question2',
                'question3',
                'question4',
                'question5',
                'question6',
                'question7',
                'question8',
                'question9',
                'question10',
                'question11',
                'question12',
            )
        }),

        ('Prerequisites', {
            'fields': ('prerequisite','eligible_groups')
        }),

        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Materials)
class MaterialsAdmin(admin.ModelAdmin):
    list_display = ('event','title', 'level', 'status_display', 'status_toggle', 'created_at')
    list_filter = ('event', 'level', 'status')
    search_fields = ('event__event_name', 'level__name')
    filter_horizontal = ('completed_users',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title','event', 'level')
        }),
        ('Content', {
            'fields': ('link', 'pdf_file')
        }),
        ('Settings', {
            'fields': ('status', 'completed_users')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('event', 'level')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('toggle-material-status/', self.admin_site.admin_view(self.toggle_material_status),
                 name='toggle-material-status'),
        ]
        return custom_urls + urls

    def toggle_material_status(self, request):
        material_id = request.GET.get('id')
        try:
            material = Materials.objects.get(id=material_id)
            # Toggle the status
            new_status = 'inactive' if material.status == 'active' else 'active'
            material.status = new_status
            material.save()
            messages.success(request, f'Material status changed to {new_status}')
        except Materials.DoesNotExist:
            messages.error(request, 'Material not found')

        # Redirect back to the list view
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:index')))

    def status_display(self, obj):
        if obj.status == 'active':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Inactive</span>'
        )

    status_display.short_description = 'Status'

    def status_toggle(self, obj):
        return format_html(
            '''
            <div style="width: 32px; height: 16px; background-color: {}; border-radius: 8px; position: relative; cursor: pointer;">
                <a href="{}?id={}" style="display: block; width: 100%; height: 100%; text-decoration: none;">
                    <span style="width: 12px; height: 12px; background-color: white; border-radius: 50%; position: absolute; top: 2px; {}"></span>
                </a>
            </div>
            ''',
            '#28a745' if obj.status == 'active' else '#dc3545',
            reverse('admin:toggle-material-status'),
            obj.id,
            'right: 2px;' if obj.status == 'active' else 'left: 2px;'
        )

    status_toggle.short_description = 'Toggle'

class SlotGroupInline(admin.TabularInline):
    model = SlotGroup
    extra = 1
    fields = (
    'group_name', 'event', 'level', 'topic', 'start_time', 'end_time', 'date', 'total_rankings', 'start_status')


class SlotParticipantInline(admin.TabularInline):
    model = SlotParticipant
    extra = 0
    fields = ('user', 'group_name', 'participant_status', 'joined', 'voting_status', 'finished_level', 'topic')
    readonly_fields = ('group_name',)
    can_delete = False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')



@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = (
        'slot_id',
        'created_by',
        'assigned_to',
        'staff_id',
        'venue',
        'slot_status_display',
        'created_at',
        'get_group_count',
        'get_participant_count'
    )
    list_filter = (
        ('created_at', DateRangeFilter),
        'slot_status',
        'venue',
    )
    search_fields = (
        'slot_id',
        'created_by__name',
        'staff_id',
        'venue__venue_name'
    )
    readonly_fields = (
        'slot_id',
        'created_at',
        'updated_at',
        'staff_id'
    )
    inlines = [SlotGroupInline]

    def slot_status_display(self, obj):
        if obj.slot_status == 'live':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Live</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Expired</span>'
        )

    slot_status_display.short_description = 'Status'

    def get_group_count(self, obj):
        return obj.groups.count()

    get_group_count.short_description = 'Groups'

    def get_participant_count(self, obj):
        return SlotParticipant.objects.filter(slot=obj).count()

    get_participant_count.short_description = 'Participants'

    def save_model(self, request, obj, form, change):
        # If this is a new slot being created
        if not change:
            # Set the creator if not already set
            if not obj.created_by and request.user.is_authenticated:
                try:
                    obj.created_by = request.user.userprofile
                except:
                    pass

        super().save_model(request, obj, form, change)

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'slot_id',
                'created_by',
                'assigned_to',
                'staff_id',
                'venue',
                'slot_status'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SlotGroup)
class SlotGroupAdmin(admin.ModelAdmin):
    list_display = (
        'slot',
        'group_name',
        'event',
        'level',
        'topic',
        'date',
        'formatted_start_time',
        'formatted_end_time',
        'start_status_display',
        'get_participant_count','finished',
    )
    list_filter = (
        ('date', DateRangeFilter),
        'event',
        'level',
        'start_status',
        'slot'
    )
    search_fields = (
        'group_name',
        'slot__slot_id',
        'event__event_name',
        'level__name',
        'topic__topic_name'
    )
    filter_horizontal = ('participants',)

    # Add these methods to format time display
    def formatted_start_time(self, obj):
        if obj.start_time:
            return obj.start_time.strftime('%I:%M %p')  # 12-hour format with AM/PM
        return "Not set"

    formatted_start_time.short_description = 'Start Time'

    def formatted_end_time(self, obj):
        if obj.end_time:
            return obj.end_time.strftime('%I:%M %p')  # 12-hour format with AM/PM
        return "Not set"

    formatted_end_time.short_description = 'End Time'


    def start_status_display(self, obj):
        status_colors = {
            'start': '#28a745',  # green
            'pause': '#ffc107',  # yellow
            'end': '#dc3545'  # red
        }
        status_labels = {
            'start': 'Started',
            'pause': 'Paused',
            'end': 'Ended'
        }
        color = status_colors.get(obj.start_status, '#6c757d')  # default gray
        label = status_labels.get(obj.start_status, obj.start_status.capitalize())

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, label
        )

    start_status_display.short_description = 'Status'

    def get_participant_count(self, obj):
        return obj.participants.count()

    get_participant_count.short_description = 'Participants'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "topic":
            if request.resolver_match.kwargs.get('object_id'):
                group = SlotGroup.objects.get(pk=request.resolver_match.kwargs['object_id'])
                kwargs["queryset"] = Topic.objects.filter(level=group.level)
            else:
                kwargs["queryset"] = Topic.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Calculate end_time based on start_time and level's duration if not provided


        if not obj.end_time and obj.start_time and obj.level:
            start_time = datetime.combine(datetime.today(), obj.start_time)
            duration_minutes = obj.level.total_duration
            end_time = start_time + timedelta(minutes=duration_minutes)
            obj.end_time = end_time.time()

        super().save_model(request, obj, form, change)

        # Handle start_status change to 'start'
        if 'start_status' in form.changed_data and obj.start_status == 'start':
            # Ensure participants have SlotParticipant entries
            self.create_participant_entries(obj)

            # If a topic is assigned, make sure all participants get the same topic
            if obj.topic:
                SlotParticipant.objects.filter(
                    slot=obj.slot,
                    group_name=obj.group_name
                ).update(topic=obj.topic)

        # Handle start_status change to 'end'
        if 'start_status' in form.changed_data and obj.start_status == 'end':
            # Mark all participants as completed
            SlotParticipant.objects.filter(
                slot=obj.slot,
                group_name=obj.group_name
            ).update(
                participant_status='completed',
                finished_level=True
            )

    def create_participant_entries(self, obj):
        """Create SlotParticipant entries for all participants in this group"""
        current_participants = obj.participants.all()

        for user in current_participants:
            SlotParticipant.objects.update_or_create(
                slot=obj.slot,
                group_name=obj.group_name,
                user=user,
                defaults={
                    'topic': obj.topic,
                    'participant_status': 'on_going',
                    'joined': False,
                    'voting_status': 'not_started',
                    'voting_progress': {},
                    'finished_level': False
                }
            )

    fieldsets = (
        ('Group Information', {
            'fields': (
                'slot',
                'group_name',
                'total_rankings',
            )
        }),
        ('Event Details', {
            'fields': (
                'event',
                'level',
                'topic',
            )
        }),
        ('Schedule', {
            'fields': (
                'date',
                'start_time',
                'end_time','metadata',
            )
        }),
        ('Participants', {
            'fields': ('participants',),
            'description': 'Users assigned to this group.'
        }),
        ('Status Controls', {
            'fields': ('start_status','finished'),
            'description': 'Control the status of this group session.'
        }),
    )


@admin.register(SlotParticipant)
class SlotParticipantAdmin(admin.ModelAdmin):
    list_display = (
        'get_user_name',
        'get_roll_number',
        'get_slot_id',
        'group_name',
        'get_event_name',
        'get_level_name',
        'participant_status',
        'voting_status',
        'joined_status',
        'finished_level_status'
    )

    list_filter = (
        'participant_status',
        'voting_status',
        'joined',
        'finished_level',
        'group_name',
        'slot__created_at'
    )

    search_fields = (
        'user__name',
        'user__roll_number',
        'user__mail_id',
        'slot__slot_id',
        'group_name'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'group_name'
    )

    actions = [
        'mark_as_joined',
        'mark_as_not_joined',
        'set_voting_not_started',
        'set_voting_in_progress',
        'set_voting_finished'
    ]

    def mark_as_joined(self, request, queryset):
        updated = queryset.update(joined=True)
        self.message_user(request, f"{updated} participants marked as joined.")

    mark_as_joined.short_description = "Mark selected participants as joined"

    def mark_as_not_joined(self, request, queryset):
        updated = queryset.update(joined=False)
        self.message_user(request, f"{updated} participants marked as not joined.")

    mark_as_not_joined.short_description = "Mark selected participants as not joined"

    def set_voting_not_started(self, request, queryset):
        updated = queryset.update(voting_status='not_started')
        self.message_user(request, f"Changed voting status to 'not started' for {updated} participants.")

    set_voting_not_started.short_description = "Set voting status to 'Not Started'"

    def set_voting_in_progress(self, request, queryset):
        updated = queryset.update(voting_status='in_progress')
        self.message_user(request, f"Changed voting status to 'in progress' for {updated} participants.")

    set_voting_in_progress.short_description = "Set voting status to 'In Progress'"

    def set_voting_finished(self, request, queryset):
        updated = queryset.update(voting_status='finished')
        self.message_user(request, f"Changed voting status to 'finished' for {updated} participants.")

    set_voting_finished.short_description = "Set voting status to 'Finished'"

    def get_user_name(self, obj):
        return obj.user.name


    get_user_name.short_description = 'Name'
    get_user_name.admin_order_field = 'user__name'

    def get_roll_number(self, obj):
        return obj.user.roll_number or obj.user.staff_id

    get_roll_number.short_description = 'ID'
    get_roll_number.admin_order_field = 'user__roll_number'

    def get_slot_id(self, obj):
        return obj.slot.slot_id

    get_slot_id.short_description = 'Slot ID'
    get_slot_id.admin_order_field = 'slot__slot_id'

    def get_event_name(self, obj):
        # Need to get the event from the SlotGroup
        try:
            group = SlotGroup.objects.get(slot=obj.slot, group_name=obj.group_name)
            return group.event.event_name
        except SlotGroup.DoesNotExist:
            return "N/A"

    get_event_name.short_description = 'Event'

    def get_level_name(self, obj):
        # Need to get the level from the SlotGroup
        try:
            group = SlotGroup.objects.get(slot=obj.slot, group_name=obj.group_name)
            return f"Level {group.level.level}"
        except SlotGroup.DoesNotExist:
            return "N/A"

    get_level_name.short_description = 'Level'

    def joined_status(self, obj):
        if obj.joined:
            return format_html('<span style="color: green; font-weight: bold;">✓</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗</span>')

    joined_status.short_description = 'Joined'

    def finished_level_status(self, obj):
        if obj.finished_level:
            return format_html('<span style="color: green; font-weight: bold;">✓</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗</span>')

    finished_level_status.short_description = 'Finished'

    fieldsets = (
        ('Slot Information', {
            'fields': ('slot', 'user', 'group_name')
        }),
        ('Participation Details', {
            'fields': (
                'participant_status',
                'joined',
                'voting_status',
                'voting_progress',
                'topic',
                'finished_level','mark','request_voting',
            )
        }),

        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def has_add_permission(self, request):
        return False  # SlotParticipants should only be created through SlotGroup


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('topic_name', 'level', 'get_event')
    list_filter = ('level', 'level__event')
    search_fields = ('topic_name', 'level__name', 'level__event__event_name')

    def get_event(self, obj):
        return obj.level.event.event_name

    get_event.short_description = 'Event'
    get_event.admin_order_field = 'level__event__event_name'

    fieldsets = (
        ('Topic Information', {
            'fields': (
                'topic_name',
                'level'
            )
        }),
    )


@admin.register(Achievements)
class AchievementsAdmin(admin.ModelAdmin):
    list_display = ('name', 'mail_id', 'department', 'finished_level','group_name','mark', 'created_at')
    search_fields = ('name', 'mail_id')
    list_filter = ('department', 'finished_level')
    readonly_fields = ('name', 'mail_id', 'department', 'event','level','created_at', 'updated_at')

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'name', 'mail_id', 'department')
        }),
        ('Achievements', {
            'fields': ('finished_level','event','level','mark','slot_id','group_name')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        # Attempt to populate additional fields from UserProfile
        if obj.user:
            try:
                user_profile = UserProfile.objects.get(user=obj.user)
                obj.name = user_profile.name
                obj.mail_id = user_profile.mail_id
                obj.department = user_profile.department
            except UserProfile.DoesNotExist:
                messages.warning(request, f'No profile found for selected user {obj.user.username}')

        super().save_model(request, obj, form, change)



##### QUICK SLOTS ADMIN



