from datetime import datetime

def calculate_age_from_dob(dob_str):
    """
    Calculates age from a DOB string.
    
    IMPORTANT: 
    Your Flutter app sends the date as "DD-MM-YYYY" (e.g., "25-12-1995").
    Therefore, we must use the format "%d-%m-%Y" here.
    """
    if not dob_str:
        return 0 # Return 0 to prevent DB errors for Integer columns

    try:
        # Parse the string: Day (d) - Month (m) - Year (Y)
        birth_date = datetime.strptime(dob_str, "%d-%m-%Y")
        
        today = datetime.now()
        
        # Calculate age accurately
        # Formula: Current Year - Birth Year - (1 if birthday hasn't happened yet this year)
        age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
        
        return age
    except ValueError:
        print(f"⚠️ Invalid DOB format received: {dob_str}. Expected DD-MM-YYYY")
        return 0