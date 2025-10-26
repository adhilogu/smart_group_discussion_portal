from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import UserProfile


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get('email', '')
        print(f"Logging in with email: {email}")  # Debugging
        if not email.endswith('@yourdomain.com'):
            print("Login blocked: Email domain not allowed")  # Debugging
            return  # Make sure you are not blocking all users!

        # If this is a new user, set up their profile
        if not sociallogin.is_existing:
            # Get or create user data from the social account
            user = sociallogin.user
            user_data = sociallogin.account.extra_data

            # Set any additional user attributes
            user.first_name = user_data.get('given_name', '')
            user.last_name = user_data.get('family_name', '')
            user.save()

            # Set up a UserProfile for this user
            try:
                user_profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                user_profile = UserProfile(user=user)
                user_profile.name = f"{user.first_name} {user.last_name}".strip()
                user_profile.mail_id = email

                # Set other fields as needed
                if email.endswith('@yourdomain.com'):
                    # Determine if this is a student or faculty email and set fields accordingly
                    if 'student' in email or any(char.isdigit() for char in email.split('@')[0]):
                        user_profile.user_type = 'STUDENT'
                        # Extract roll number if possible
                        possible_roll = ''.join(filter(str.isdigit, email.split('@')[0]))
                        if possible_roll:
                            user_profile.roll_number = possible_roll
                    else:
                        user_profile.user_type = 'FACULTY'
                        # Set staff_id if you have a way to determine it

                user_profile.status = 'active'
                user_profile.save()

