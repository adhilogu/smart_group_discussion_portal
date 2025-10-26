from datetime import timezone, time

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import random
import string
from django.db.models import JSONField  # Import JSONField
from django.contrib.auth.models import Group

USE_TZ = True
TIME_ZONE = 'Asia/Kolkata'


class UserProfile(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    BATCH_CHOICES = (
        ('2022-2026', '2022-2026'),
        ('2023-2027', '2023-2027'),
    )
    DEPARTMENT_CHOICES = (
        # B.E. Programs
        ('BE-BME', 'B.E. - BIOMEDICAL ENGINEERING'),
        ('BE-EIE', 'B.E. - ELECTRONICS AND INSTRUMENTATION ENGINEERING'),
        ('BE-ECE', 'B.E. - ELECTRONICS AND COMMUNICATION ENGINEERING'),
        ('BE-EEE', 'B.E. - ELECTRICAL AND ELECTRONICS ENGINEERING'),
        ('BE-CSE', 'B.E. - COMPUTER SCIENCE AND ENGINEERING'),
        ('BE-CSD', 'B.E. - COMPUTER SCIENCE AND DESIGN'),
        ('BE-CIVIL', 'B.E. - CIVIL ENGINEERING'),
        ('BE-ISE', 'B.E. - INFORMATION SCIENCE AND ENGINEERING'),
        ('BE-MECH', 'B.E. - MECHANICAL ENGINEERING'),
        ('BE-MCT', 'B.E. - MECHATRONICS ENGINEERING'),

        # B.Tech. Programs
        ('BTECH-BT', 'B.Tech. - BIOTECHNOLOGY'),
        ('BTECH-AGE', 'B.Tech. - AGRICULTURAL ENGINEERING'),
        ('BTECH-AIDS', 'B.Tech. - ARTIFICIAL INTELLIGENCE AND DATA SCIENCE'),
        ('BTECH-AIML', 'B.Tech. - ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING'),
        ('BTECH-CSBS', 'B.Tech. - COMPUTER SCIENCE AND BUSINESS SYSTEMS'),
        ('BTECH-CT', 'B.Tech. - COMPUTER TECHNOLOGY'),
        ('BTECH-FT', 'B.Tech. - FASHION TECHNOLOGY'),
        ('BTECH-FDT', 'B.Tech. - FOOD TECHNOLOGY'),
        ('BTECH-IT', 'B.Tech. - INFORMATION TECHNOLOGY'),

        # M.E. Programs
        ('ME-CS', 'M.E. - COMMUNICATION SYSTEMS'),
        ('ME-CSE', 'M.E. - COMPUTER SCIENCE AND ENGINEERING'),
        ('ME-ISE', 'M.E. - INDUSTRIAL SAFETY ENGINEERING'),
        ('ME-SE', 'M.E. - STRUCTURAL ENGINEERING'),

        # MBA
        ('MBA', 'M.B.A. - MASTER OF BUSINESS ADMINISTRATION'),

        # Ph.D. Programs
        ('PHD-BT', 'Ph.D BIOTECHNOLOGY'),
        ('PHD-CHEM', 'Ph.D CHEMISTRY'),
        ('PHD-CIVIL', 'Ph.D CIVIL ENGINEERING'),
        ('PHD-CSE', 'Ph.D COMPUTER SCIENCE AND ENGINEERING'),
        ('PHD-EEE', 'Ph.D ELECTRICAL AND ELECTRONICS ENGINEERING'),
        ('PHD-ECE', 'Ph.D ELECTRONICS AND COMMUNICATION ENGINEERING'),
        ('PHD-EIE', 'Ph.D ELECTRONICS AND INSTRUMENTATION ENGINEERING'),
        ('PHD-IT', 'Ph.D INFORMATION TECHNOLOGY'),
        ('PHD-MATH', 'Ph.D MATHEMATICS'),
        ('PHD-MECH', 'Ph.D MECHANICAL ENGINEERING'),
        ('PHD-MCT', 'Ph.D MECHATRONICS'),
        ('PHD-PHY', 'Ph.D PHYSICS'),
        ('PHD-SMS', 'Ph.D SCHOOL OF MANAGEMENT STUDIES'),

        # Departments
        ('ELCC', 'ELCC'),
        ('DEPT-PHY', 'DEPARTMENT OF PHYSICS'),
        ('DEPT-MATH', 'DEPARTMENT OF MATHEMATICS'),
        ('DEPT-CHEM', 'DEPARTMENT OF CHEMISTRY'),
    )


    GENDER_CHOICE= (
        ('MALE', 'MALE'),
        ('FEMALE', 'FEMALE'),

    )

    USERTYPE_CHOICE = (
        ('STUDENT', 'STUDENT'),
        ('FACULTY', 'FACULTY'),

    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True,null=True, blank=True)
    user_type=  models.CharField(max_length=50, choices=USERTYPE_CHOICE,null=True, blank=True)
    staff_id = models.CharField(max_length=20, unique=True,null=True, blank=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES,null=True, blank=True)
    gender=models.CharField(max_length=50, choices=GENDER_CHOICE,null=True, blank=True)
    batch = models.CharField(max_length=10,null=True,choices=BATCH_CHOICES, blank=True)
    phone_number = models.CharField(max_length=15)
    mail_id = models.EmailField(unique=True)
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True,
                                        help_text="Telegram chat ID for notifications")

    def __str__(self):
        if self.roll_number:
            return f"{self.name} - {self.roll_number} - {self.mail_id}"
        elif self.staff_id:
            return f"{self.name} - {self.staff_id} - {self.mail_id}"
        else:
            return f"{self.name} - {self.mail_id}"

    class Meta:
        ordering = ['name']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class Event(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    event_name = models.CharField(max_length=100, unique=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )
    eligible_groups = models.ManyToManyField(
        Group,
        related_name='event',
        blank=True,
        help_text="If empty, slot is available to everyone. Otherwise, only specified groups are eligible."
    )

    event_photo = models.ImageField(upload_to='event_photo/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def is_eligible_for_user(self, user):
        """Check if a user is eligible for this slot based on their groups"""
        # If no eligible groups are specified, everyone is eligible
        if not self.eligible_groups.exists():
            return True

        # Check if any of user's groups match eligible groups
        user_groups = user.groups.all()
        return self.eligible_groups.filter(id__in=user_groups).exists()

    def __str__(self):
        return self.event_name

    class Meta:
        ordering = ['event_name']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'


class Levels(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )

    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        related_name='levels'
    )
    name = models.CharField(max_length=100)
    level = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Level number (e.g., 1, 2, 3)"
    )

    total_duration = models.PositiveIntegerField(
        verbose_name="Total Duration (minutes)",
        default=0
    )

    # Agenda timings
    agenda1_name = models.CharField(
        verbose_name="Agenda 1 Name",
        max_length=100,
        null=True, blank=True
    )
    agenda1_duration = models.PositiveIntegerField(
        verbose_name="Agenda 1 Duration (minutes)",
        null=True, blank=True,
        validators=[MinValueValidator(1)]
    )

    agenda2_name = models.CharField(
        verbose_name="Agenda 2 Name",
        max_length=100,
        null=True, blank=True
    )
    agenda2_duration = models.PositiveIntegerField(
        verbose_name="Agenda 2 Duration (minutes)",
        null=True, blank=True,
        validators=[MinValueValidator(1)]
    )

    agenda3_name = models.CharField(
        verbose_name="Agenda 3 Name",
        max_length=100,
        null=True, blank=True
    )
    agenda3_duration = models.PositiveIntegerField(
        verbose_name="Agenda 3 Duration (minutes)",
        null=True, blank=True,
        validators=[MinValueValidator(1)]
    )

    agenda4_name = models.CharField(
        verbose_name="Agenda 4 Name",
        max_length=100,
        null=True, blank=True
    )
    agenda4_duration = models.PositiveIntegerField(
        verbose_name="Agenda 4 Duration (minutes)",
        null=True, blank=True,
        validators=[MinValueValidator(1)]
    )

    agenda5_name = models.CharField(
        verbose_name="Agenda 5 Name",
        max_length=100,
        null=True, blank=True
    )
    agenda5_duration = models.PositiveIntegerField(
        verbose_name="Agenda 5 Duration (minutes)",
        null=True, blank=True,
        validators=[MinValueValidator(1)]
    )

    eligible_groups = models.ManyToManyField(
        Group,
        related_name='eligible_slots',
        blank=True,
        help_text="If empty, slot is available to everyone. Otherwise, only specified groups are eligible."
    )

    agenda6_name = models.CharField(
        verbose_name="Agenda 6 Name",
        max_length=100,
        null=True, blank=True
    )
    agenda6_duration = models.PositiveIntegerField(
        verbose_name="Agenda 6 Duration (minutes)",
        null=True, blank=True,
        validators=[MinValueValidator(1)]
    )

    agenda7_name = models.CharField(
        verbose_name="Agenda 7 Name",
        max_length=100,
        null=True, blank=True
    )
    agenda7_duration = models.PositiveIntegerField(
        verbose_name="Agenda 7 Duration (minutes)",
        null=True, blank=True,
        validators=[MinValueValidator(1)]
    )

    agenda8_name = models.CharField(
        verbose_name="Agenda 8 Name",
        max_length=100,
        null=True, blank=True
    )
    agenda8_duration = models.PositiveIntegerField(
        verbose_name="Agenda 8 Duration (minutes)",
        null=True, blank=True,
        validators=[MinValueValidator(1)]
    )

    agenda9_name = models.CharField(
        verbose_name="Agenda 9 Name",
        max_length=100,
        null=True, blank=True
    )
    agenda9_duration = models.PositiveIntegerField(
        verbose_name="Agenda 9 Duration (minutes)",
        null=True, blank=True,
        validators=[MinValueValidator(1)]
    )

    agenda10_name = models.CharField(
        verbose_name="Agenda 10 Name",
        max_length=100,
        null=True, blank=True
    )
    agenda10_duration = models.PositiveIntegerField(
        verbose_name="Agenda 10 Duration (minutes)",
        null=True, blank=True,
        validators=[MinValueValidator(1)]
    )

    # Questions
    question1 = models.TextField(blank=True)
    question2 = models.TextField(blank=True)
    question3 = models.TextField(blank=True)
    question4 = models.TextField(blank=True)
    question5 = models.TextField(blank=True)
    question6 = models.TextField(blank=True)
    question7 = models.TextField(blank=True)
    question8 = models.TextField(blank=True)
    question9 = models.TextField(blank=True)
    question10 = models.TextField(blank=True)
    question11 = models.TextField(blank=True)
    question12 = models.TextField(blank=True)

    prerequisite = models.ForeignKey(
        'self',  # References the same model
        on_delete=models.SET_NULL,  # If prerequisite level is deleted, set to NULL
        null=True,
        blank=True,
        related_name='dependent_levels',
        verbose_name="Prerequisite Level",
        help_text="Level that must be completed before this one"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def is_eligible_for_user(self, user):
        """Check if a user is eligible for this slot based on their groups"""
        # If no eligible groups are specified, everyone is eligible
        if not self.eligible_groups.exists():
            return True

        # Check if any of user's groups match eligible groups
        user_groups = user.groups.all()
        return self.eligible_groups.filter(id__in=user_groups).exists()




    def __str__(self):
        return f"{self.event.event_name} - Level {self.level} - {self.name} "

    class Meta:
        ordering = ['event', 'level', 'name']
        verbose_name = 'Level'
        verbose_name_plural = 'Levels'

class Venue(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    venue_name = models.CharField(max_length=100, unique=True)
    venue_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum capacity of the venue"
    )

    filled_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Filled capacity in the venue"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.venue_name

    class Meta:
        ordering = ['venue_name']
        verbose_name = 'Venue'
        verbose_name_plural = 'Venues'


class Topic(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    topic_name = models.TextField(max_length=3000,unique=True)
    level = models.ForeignKey(
        'Levels',
        on_delete=models.CASCADE,
        related_name='topics'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    def __str__(self):
        return f"{self.topic_name}"

    class Meta:
        ordering = ['level', 'topic_name']
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'


class Materials(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        related_name='materials'
    )

    level = models.ForeignKey(
        'Levels',
        on_delete=models.CASCADE,
        related_name='materials'
    )

    title = models.CharField(max_length=200)

    link = models.URLField(
        blank=True,
        null=True,
        help_text="External link to the material"
    )

    pdf_file = models.FileField(
        upload_to='materials/pdfs/',
        blank=True,
        null=True,
        help_text="PDF file for the material"
    )

    completed_users = models.ManyToManyField(
        User,
        related_name='completed_materials',
        blank=True,
        help_text="Users who have completed this material"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.event.event_name} (Level: {self.level.name})"

    class Meta:
        verbose_name = 'Material'
        verbose_name_plural = 'Materials'
        ordering = ['-created_at']


class Slot(models.Model):
    SLOT_STATUS_CHOICES = (
        ('live', 'Live'),
        ('expired', 'Expired'),
    )

    slot_id = models.CharField(
        max_length=5,
        unique=True,
        editable=False,
        help_text="Unique 5-digit slot identifier"
    )
    created_by = models.ForeignKey(
        'UserProfile',
        on_delete=models.SET_NULL,
        related_name='created_slots',
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'FACULTY'},
        verbose_name="Created By"
    )

    assigned_to = models.ForeignKey(
        'UserProfile',
        on_delete=models.SET_NULL,
        related_name='assigned_slots_new',
        null=True,
        blank=True,
        limit_choices_to={
            'user__groups__name__in': [
                'faculty',
                'slot host',
                'slot creator'
            ]
        },
        verbose_name="Assigned To"
    )

    staff_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Staff ID"
    )
    venue = models.ForeignKey(
        'Venue',
        on_delete=models.CASCADE,
        related_name='slots',
        null=True, blank=True
    )
    slot_status = models.CharField(
        max_length=10,
        choices=SLOT_STATUS_CHOICES,
        default='live'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)





    def generate_slot_id(self):
        # Generate a random 5-digit code
        while True:
            code = ''.join(random.choices(string.digits, k=5))
            if not Slot.objects.filter(slot_id=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.slot_id:
            self.slot_id = self.generate_slot_id()

        if self.created_by and not self.staff_id:
            self.staff_id = self.created_by.staff_id or ""

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Slot {self.slot_id}"

    class Meta:
        verbose_name = 'Slot'
        verbose_name_plural = 'Slots'


class SlotGroup(models.Model):
    START_STATUS_CHOICES = (
        ('start', 'Start'),
        ('pause', 'Pause'),
        ('end', 'End'),
    )

    slot = models.ForeignKey(
        Slot,
        on_delete=models.CASCADE,
        related_name='groups'
    )
    group_name = models.CharField(
        max_length=4,
        help_text="Alphabetic group identifier (e.g., A12, B45)"
    )
    total_rankings = models.PositiveIntegerField(

        validators=[MinValueValidator(1)],null=True, blank=True,
        help_text="Total number of ranking positions"
    )
    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        related_name='slot_groups'
    )
    level = models.ForeignKey(
        'Levels',
        on_delete=models.CASCADE,
        related_name='slot_groups'
    )
    topic = models.ForeignKey(
        'Topic',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='slot_groups'
    )

    metadata = models.JSONField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)
    date = models.DateField()
    participants = models.ManyToManyField(
        'UserProfile',
        related_name='groups',
        blank=True
    )
    start_status = models.CharField(
        max_length=10,
        choices=START_STATUS_CHOICES,
        default='pause',
        verbose_name="Start Status"
    )

    finished = models.BooleanField(
        default=False,
        verbose_name="Group Finished",
        help_text="Indicates whether the group has completed all its activities"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # First save the model to ensure we have a primary key
        super().save(*args, **kwargs)

        # After saving, ensure all participants have SlotParticipant entries
        if self.pk:  # Only run this if we have a primary key (not a new object)
            current_participants = self.participants.all()

            # Create or update SlotParticipant entries for each participant
            for user in current_participants:
                # First check if the participant already exists
                existing_participant = SlotParticipant.objects.filter(
                    slot=self.slot,
                    group_name=self.group_name,
                    user=user
                ).first()

                if existing_participant:
                    # Only update the topic if it has changed
                    if existing_participant.topic != self.topic:
                        existing_participant.topic = self.topic
                        existing_participant.save(update_fields=['topic'])
                else:
                    # Create a new participant entry for users who don't have one yet
                    SlotParticipant.objects.create(
                        slot=self.slot,
                        group_name=self.group_name,
                        user=user,
                        topic=self.topic,
                        participant_status='on_going',
                        joined=False,
                        voting_status='not_started',
                        finished_level=False
                    )

    def __str__(self):
        return f"Slot {self.slot.slot_id} - Group {self.group_name}"

    class Meta:
        unique_together = ['slot', 'group_name']
        verbose_name = 'Slot Group'
        verbose_name_plural = 'Slot Groups'


class SlotParticipant(models.Model):
    PARTICIPANT_STATUS_CHOICES = (
        ('on_going', 'On Going'),
        ('completed', 'Completed')
    )

    VOTING_REQUEST = (
        ('request', 'request'),
        ('not_requested', 'not_requested'),

    )

    VOTING_STATUS_CHOICES = (
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('finished', 'Finished')
    )

    slot = models.ForeignKey(
        Slot,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    group_name = models.CharField(
        max_length=10,
        help_text="Alphabetic group identifier (e.g., A12, B45)"
    )
    user = models.ForeignKey(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='participations'
    )
    topic = models.ForeignKey(
        'Topic',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    participant_status = models.CharField(
        max_length=20,
        choices=PARTICIPANT_STATUS_CHOICES,
        default='on_going'
    )
    joined = models.BooleanField(
        default=False,
        help_text="Indicates if the user has joined the slot"
    )
    voting_status = models.CharField(
        max_length=20,
        choices=VOTING_STATUS_CHOICES,
        default='not_started'
    )
    request_voting = models.CharField(
        max_length=20,
        choices=VOTING_REQUEST, #-#
        default='not_requested'
    )
    voting_progress = models.JSONField(
        null=True,
        blank=True,
        help_text="Stores voting progress and marks for each question"
    )
    finished_level = models.BooleanField(
        default=False,
        help_text="Indicates if the user has completed this level"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    mark = models.FloatField(
        null=True,
        blank=True,
        help_text="Mark assigned to the participant"
    )

    class Meta:
        unique_together = ['slot', 'group_name', 'user']
        verbose_name = 'Slot Participant'
        verbose_name_plural = 'Slot Participants'

    def __str__(self):
        joined_status = "✓" if self.joined else "✗"
        return f"{self.user.name} - Group {self.group_name} - Joined: {joined_status}"


class Achievements(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    name = models.CharField(max_length=100, editable=False)  # Made read-only
    mail_id = models.EmailField(editable=False)  # Made read-only
    department = models.CharField(
        max_length=50,
        choices=UserProfile.DEPARTMENT_CHOICES,
        null=True,
        blank=True,
        editable=False  # Made read-only
    )
    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        related_name='achievements'
    )

    # Added mark field to store the user's score
    mark = models.FloatField(null=True, blank=True)

    # Added slot and group information
    slot_id = models.CharField(max_length=10, null=True, blank=True)
    group_name = models.CharField(max_length=10, null=True, blank=True)

    finished_level = models.ForeignKey(
        'Levels',
        on_delete=models.SET_NULL,
        related_name='achieved_by',
        null=True,
        blank=True
    )
    level = models.PositiveIntegerField(
        editable=False,  # Made read-only since it should match finished_level.level
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.finished_level:
            self.level = self.finished_level.level
            self.event = self.finished_level.event

        # Get user details from UserProfile if available
        if hasattr(self.user, 'userprofile'):
            self.name = self.user.userprofile.name
            self.mail_id = self.user.email
            self.department = self.user.userprofile.department

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.finished_level} (Mark: {self.mark})"

    class Meta:
        ordering = ['event', 'level', '-mark']
        verbose_name = 'Achievement'
        verbose_name_plural = 'Achievements'
        unique_together = ('user', 'finished_level', 'slot_id', 'group_name')


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    # Link to the relevant object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    action_url = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']

#QUICK SLOT MODEL#################

