"""Message templates for outreach"""
from typing import Dict

OUTREACH_TEMPLATES: Dict[str, str] = {
    "email_intro": """
Hi {{ company.name }} team,

I hope this email finds you well. My name is [Your Name] from TowPilot, and I'm reaching out because I noticed your towing company serves the {{ company.address_city }} area.

We've built something that could help streamline your dispatch operations and potentially increase your revenue. I'd love to share more about our free mastermind and educational offering that we're providing to towing companies like yours.

Would you be open to a quick 15-minute conversation this week?

Best regards,
[Your Name]
TowPilot Team
""",
    
    "sms_intro": """
Hi {{ company.name }}! This is [Name] from TowPilot. We help towing companies in {{ company.address_city }} streamline operations. Would you be open to a quick call this week? Free educational resources available!
""",
    
    "phone_script": """
Hello, this is [Your Name] from TowPilot. I'm calling to introduce our free mastermind and educational program for towing companies. We help businesses like yours streamline dispatch operations. Would you have 15 minutes to chat this week?
"""
}

