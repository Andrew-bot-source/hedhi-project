from django.contrib import admin

# Register your models here.


from .models import (
    CycleProfile,
    CycleRecord,
    SymptomLog,
    NotificationPreference,
)


admin.site.register(CycleProfile)
admin.site.register(CycleRecord)
admin.site.register(SymptomLog)
admin.site.register(NotificationPreference)