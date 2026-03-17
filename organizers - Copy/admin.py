from django.contrib import admin
from .models import OrganizerProfile, OrganizerTeamMember, EventAnalytics, EventTemplate, OrganizerNotification, OrganizerPayout

admin.site.register(OrganizerProfile)
admin.site.register(OrganizerTeamMember)
admin.site.register(EventAnalytics)
admin.site.register(EventTemplate)
admin.site.register(OrganizerNotification)
admin.site.register(OrganizerPayout)
