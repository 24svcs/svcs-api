import random


def generate_unique_employee_id():
    while True:
        # Generate a random 8-digit number
        employee_id = str(random.randint(10000000, 99999999))
        
        # Check if this ID already exists
        if not Employee.objects.filter(id=employee_id).exists():
            return employee_id