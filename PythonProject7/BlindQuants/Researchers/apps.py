from django.apps import AppConfig

print(">>>> TRYING TO LOAD Researchers/apps.py <<<<") # Add this

class BasicResearchersConfig(AppConfig): # Assuming this is your main AppConfig now
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Researchers'

print(">>>> SUCCESSFULLY FINISHED Researchers/apps.py <<<<") # Add this