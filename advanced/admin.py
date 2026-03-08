from django.contrib import admin
from .models import (
    Vendor, VendorContact, Contract, VendorPayment,
    TeamMember, Task, TaskComment, TeamNotification,
    AuditLog, DataExport, PrivacySetting, SecurityEvent
)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'contact_name', 'email', 'rating', 'is_preferred', 'is_blacklisted']
    list_filter = ['category', 'is_preferred', 'is_blacklisted']
    search_fields = ['name', 'contact_name', 'email']
    ordering = ['-is_preferred', 'name']


@admin.register(VendorContact)
class VendorContactAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'event', 'contact_type', 'contact_date', 'created_by']
    list_filter = ['contact_type', 'contact_date']
    search_fields = ['vendor__name', 'notes']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['title', 'vendor', 'event', 'amount', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['title', 'vendor__name']
    ordering = ['-created_at']


@admin.register(VendorPayment)
class VendorPaymentAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'contract', 'amount', 'status', 'due_date', 'paid_date']
    list_filter = ['status', 'due_date']
    search_fields = ['vendor__name', 'invoice_number']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'role', 'department', 'is_active']
    list_filter = ['role', 'department', 'is_active']
    search_fields = ['user__email', 'event__title']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'assigned_to', 'status', 'priority', 'due_date']
    list_filter = ['status', 'priority', 'due_date']
    search_fields = ['title', 'description']
    ordering = ['due_date']


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['comment']


@admin.register(TeamNotification)
class TeamNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'content_type', 'object_id', 'created_at']
    list_filter = ['action', 'content_type', 'created_at']
    search_fields = ['description', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['user', 'action', 'content_type', 'object_id', 'description', 
                       'ip_address', 'user_agent', 'old_values', 'new_values', 'created_at']


@admin.register(DataExport)
class DataExportAdmin(admin.ModelAdmin):
    list_display = ['user', 'export_type', 'status', 'requested_at', 'completed_at']
    list_filter = ['export_type', 'status', 'requested_at']
    search_fields = ['user__email']


@admin.register(PrivacySetting)
class PrivacySettingAdmin(admin.ModelAdmin):
    list_display = ['user', 'updated_at']
    search_fields = ['user__email']


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'severity', 'user', 'ip_address', 'is_resolved', 'created_at']
    list_filter = ['event_type', 'severity', 'is_resolved', 'created_at']
    search_fields = ['description']
    ordering = ['-created_at']