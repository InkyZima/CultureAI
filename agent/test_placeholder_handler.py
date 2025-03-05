#!/usr/bin/env python3

"""
Test script for the PlaceholderHandler module.

This script tests the functionality of the PlaceholderHandler class,
specifically focusing on the file-based placeholder handling.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.placeholder_handler import process_template

# Test template with standard and file-based placeholders
test_template = """
Current time: {timestamp}

Context information:
{Elementarist.txt}

Notification Sender Template Sample:
{notification_sender.txt}

{non_existent_file.txt}
"""

# Process the template
processed_template = process_template(test_template)

# Print the processed template
print("===== PROCESSED TEMPLATE =====\n")
print(processed_template)
print("\n===== END OF PROCESSED TEMPLATE =====")
