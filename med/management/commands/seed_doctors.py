import random
from decimal import Decimal
from datetime import time
from django.core.management.base import BaseCommand
from med.models import Doctor

class Command(BaseCommand):
    help = 'Seeds the database with dummy doctor records.'

    def handle(self, *args, **kwargs):
        # To avoid creating duplicate doctors, we'll clear the table first.
        self.stdout.write('Deleting existing doctor records...')
        Doctor.objects.all().delete()

        locations = [
            "Aurangabad", "Beed", "Latur", "Osmanabad", "Solapur", "Pune", "Mumbai",
            "Nagpur", "Nashik", "Thane", "Kolhapur", "Sangli", "Satara", "Jalgaon",
            "Amravati", "Akola", "Washim", "Buldhana", "Yavatmal", "Hingoli",
            "Parbhani", "Nanded"
        ]

        specialities = [
            "Fever", "Cold & Cough", "Stomach Ache", "Headache", "Diabetes", "Heart Problem",
            "Skin-related issues", "Allergies", "Arthritis", "Asthma", "Back Pain",
            "Bronchitis", "Cancer", "Cholesterol", "Depression", "Dizziness", "Fatigue",
            "Flu", "Gastritis", "Hypertension", "Insomnia", "Migraine", "Nausea", "Sinusitis"
        ]

        doctor_names = [
            ("Priya", "Sharma", "Female"), ("Rohan", "Verma", "Male"),
            ("Anjali", "Singh", "Female"), ("Vikram", "Rathore", "Male"),
            ("Sneha", "Patel", "Female"), ("Arjun", "Kumar", "Male"),
            ("Meera", "Desai", "Female"), ("Aditya", "Joshi", "Male"),
            ("Kavita", "Nair", "Female"), ("Sameer", "Gupta", "Male")
        ]

        self.stdout.write('Seeding the database with a doctor for each location/speciality combination...')

        # Create a doctor for every combination of location and speciality
        for loc in locations:
            for spec in specialities:
                # Create 2 or 3 doctors for each combination
                for _ in range(random.randint(2, 3)):
                    first_name, last_name, gender = random.choice(doctor_names)
                    name = f"Dr. {first_name} {last_name}"

                    Doctor.objects.create(
                        name=name,
                        expert=spec,
                        location=loc,
                        price=Decimal(random.randrange(400, 2501, 100)),
                        gender=gender,
                        rating=Decimal(f'{random.uniform(3.5, 5.0):.1f}'),
                        description=f"A highly-rated specialist in {spec} with over {random.randint(5, 25)} years of experience, serving the {loc} area.",
                        from_time=time(random.randint(8, 10), random.choice([0, 30])),
                        to_time=time(random.randint(17, 20), random.choice([0, 30]))
                    )

        self.stdout.write(self.style.SUCCESS(f'Successfully created {Doctor.objects.count()} doctor records.'))