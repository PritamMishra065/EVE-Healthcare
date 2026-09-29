from decimal import Decimal
from django.core.management.base import BaseCommand

from centres.models import DiagnosticCentre, DiagnosticTest


SEED = [
    {
        "name": "Apollo Diagnostics",
        "location": "Mumbai, Maharashtra",
        "tests": [
            ("Complete Blood Count (CBC)", Decimal("500.00")),
            ("Lipid Profile", Decimal("800.00")),
            ("Thyroid Panel (T3, T4, TSH)", Decimal("1200.00")),
            ("HbA1c", Decimal("600.00")),
        ],
    },
    {
        "name": "Dr. Lal PathLabs",
        "location": "Delhi, NCR",
        "tests": [
            ("Complete Blood Count (CBC)", Decimal("450.00")),
            ("Liver Function Test (LFT)", Decimal("900.00")),
            ("Kidney Function Test (KFT)", Decimal("950.00")),
            ("Vitamin D", Decimal("1100.00")),
        ],
    },
    {
        "name": "SRL Diagnostics",
        "location": "Bangalore, Karnataka",
        "tests": [
            ("Blood Sugar Fasting", Decimal("200.00")),
            ("Urine Routine", Decimal("150.00")),
            ("Chest X-Ray", Decimal("700.00")),
            ("ECG", Decimal("500.00")),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed diagnostic centres and tests"

    def handle(self, *args, **options):
        if DiagnosticCentre.objects.exists():
            self.stdout.write("Data already seeded, skipping.")
            return

        for entry in SEED:
            centre = DiagnosticCentre.objects.create(
                name=entry["name"],
                location=entry["location"],
            )
            for test_name, price in entry["tests"]:
                DiagnosticTest.objects.create(
                    name=test_name,
                    centre=centre,
                    price=price,
                )

        self.stdout.write(self.style.SUCCESS("Seeded 3 centres with tests."))
