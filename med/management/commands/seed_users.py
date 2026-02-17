import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
from accounts.models import Profile
from med.models import Doctor

class Command(BaseCommand):
    help = 'Seeds the database with a large number of dummy user records.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Deleting existing non-superuser user records...')
        # Keep superusers, delete all other users.
        User.objects.filter(is_superuser=False).delete()

        # Get or create the 'patients' and 'doctor' groups
        self.stdout.write('Ensuring user groups exist...')
        patients_group, _ = Group.objects.get_or_create(name='Patients')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')

        first_names = [
            'Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Sai', 'Reyansh', 'Ayaan', 'Krishna', 'Ishaan',
            'Saanvi', 'Aanya', 'Aadhya', 'Aaradhya', 'Ananya', 'Pari', 'Anika', 'Navya', 'Diya', 'Myra'
        ]
        last_names = [
            'Patel', 'Shah', 'Mehta', 'Desai', 'Joshi', 'Kulkarni', 'Sharma', 'Verma', 'Gupta', 'Singh',
            'Kumar', 'Yadav', 'Reddy', 'Naidu', 'Rao'
        ]

        user_count = random.randint(3000, 4000)
        self.stdout.write(f'Preparing to create {user_count} new dummy users...')

        users_to_create = []
        for i in range(user_count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)

            # Generate a unique username
            username = f'{first_name.lower()}.{last_name.lower()}{i}'
            email = f'{username}@example.com'

            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            user.set_password('password123')
            users_to_create.append(user)

        self.stdout.write('Bulk creating users...')
        # Use ignore_conflicts to prevent errors on the rare chance of a username collision
        created_users = User.objects.bulk_create(users_to_create, batch_size=1000, ignore_conflicts=True)
        self.stdout.write(f'Successfully created {len(created_users)} new users.')

        # --- Bulk create through-table records for groups ---
        self.stdout.write('Assigning users to the Patients group...')
        UserGroup = User.groups.through
        user_group_relations = [
            UserGroup(user_id=user.id, group_id=patients_group.id) for user in created_users
        ]
        UserGroup.objects.bulk_create(user_group_relations, batch_size=1000, ignore_conflicts=True)

        # --- Bulk create profiles ---
        self.stdout.write('Creating user profiles...')
        profiles_to_create = [
            Profile(
                user=user,
                age=random.randint(18, 75),
                gender=random.choice(['Male', 'Female']),
                mobile=f'9{random.randint(100000000, 999999999)}' # 10-digit mobile
            )
            for user in created_users
        ]
        Profile.objects.bulk_create(profiles_to_create, batch_size=1000)

        patient_count = len(created_users)
        self.stdout.write(self.style.SUCCESS(f'Successfully created {patient_count} patient user records.'))

        # --- Create users from Doctor objects ---
        self.stdout.write('Creating user accounts for doctors...')
        doctors = Doctor.objects.all()
        if not doctors.exists():
            self.stdout.write(self.style.WARNING('No doctors found in the database. Run `seed_doctors` first. Skipping doctor user creation.'))
        else:
            # This part is smaller, so individual creation is acceptable.
            for doctor in doctors:
                # Generate a unique username from the doctor's name and primary key
                name_parts = doctor.name.replace('Dr. ', '', 1).lower().split()
                if len(name_parts) >= 2:
                    username = f'dr.{name_parts[0]}.{name_parts[-1]}{doctor.pk}'
                    first_name = name_parts[0].capitalize()
                    last_name = ' '.join(name_parts[1:]).capitalize()
                else: # Fallback for single-word names
                    username = f'dr.{name_parts[0]}{doctor.pk}' if name_parts else f'dr_user{doctor.pk}'
                    first_name = name_parts[0].capitalize() if name_parts else 'Doctor'
                    last_name = ''
                
                email = f'{username}@medeasy.com'
                password = 'doctorpassword123'

                # Skip if a user with this username already exists
                if User.objects.filter(username=username).exists():
                    continue

                with transaction.atomic():
                    doctor_user = User.objects.create_user(
                        username=username, email=email, password=password,
                        first_name=first_name, last_name=last_name
                    )

                    doctor_user.groups.add(doctor_group)

                    # Link the doctor object to the newly created user and save it
                    doctor.user = doctor_user
                    doctor.save()

                    # Create a profile for the doctor user
                    Profile.objects.create(user=doctor_user, age=random.randint(30, 65), gender=doctor.gender, mobile=f'8{random.randint(100000000, 999999999)}')

            doctor_user_count = User.objects.filter(groups__name='Doctors').count()
            self.stdout.write(self.style.SUCCESS(f'Successfully created {doctor_user_count} doctor user records.'))

        total_users = User.objects.filter(is_superuser=False).count()
        self.stdout.write(self.style.SUCCESS(f'Total non-superuser users in database: {total_users}'))