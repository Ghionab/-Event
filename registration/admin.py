from django.contrib import admin
from .models import (
    Registration, TicketType, PromoCode, RegistrationField,
    Waitlist, Badge, CheckIn, AttendeePreference, AttendeeMessage,
    SessionAttendance, RegistrationDocument, BulkRegistrationUpload,
    BulkRegistrationRow, ManualRegistration
)


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['registration_number', 'event', 'attendee_name', 'attendee_email', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'event', 'created_at']
    search_fields = ['registration_number', 'attendee_name', 'attendee_email']
    readonly_fields = ['registration_number', 'qr_code', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('event', 'user', 'registration_number', 'status')
        }),
        ('Ticket', {
            'fields': ('ticket_type', 'total_amount', 'discount_amount', 'promo_code')
        }),
        ('Attendee Info', {
            'fields': ('attendee_name', 'attendee_email', 'attendee_phone', 'special_requests')
        }),
        ('Custom Fields', {
            'fields': ('custom_fields',),
            'classes': ('collapse',)
        }),
        ('Check-in', {
            'fields': ('checked_in_at', 'checked_in_by'),
            'classes': ('collapse',)
        }),
        ('Refund', {
            'fields': ('refund_amount', 'refund_reason', 'refunded_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BulkRegistrationUpload)
class BulkRegistrationUploadAdmin(admin.ModelAdmin):
    list_display = ['event', 'original_filename', 'status', 'total_rows', 'success_count', 'error_count', 'created_at']
    list_filter = ['status', 'created_at', 'event']
    search_fields = ['original_filename', 'event__title']
    readonly_fields = ['file', 'original_filename', 'file_name', 'file_size', 'created_at', 'completed_at']


@admin.register(BulkRegistrationRow)
class BulkRegistrationRowAdmin(admin.ModelAdmin):
    list_display = ['bulk_upload', 'row_number', 'status', 'registration', 'processed_at']
    list_filter = ['status', 'bulk_upload__event']
    search_fields = ['row_data']


@admin.register(ManualRegistration)
class ManualRegistrationAdmin(admin.ModelAdmin):
    list_display = ['attendee_name', 'event', 'attendee_email', 'ticket_type', 'status', 'created_at']
    list_filter = ['status', 'event', 'created_at']
    search_fields = ['attendee_name', 'attendee_email', 'event__title']
    readonly_fields = ['created_at', 'updated_at']
@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'ticket_category', 'price', 'quantity_available', 'quantity_sold', 'is_active']
    list_filter = ['ticket_category', 'is_active', 'event']
    search_fields = ['name', 'event__title']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'event', 'discount_type', 'discount_value', 'max_uses', 'current_uses', 'is_active']
    list_filter = ['is_active', 'discount_type', 'event']
    search_fields = ['code', 'event__title']


@admin.register(RegistrationField)
class RegistrationFieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'event', 'field_type', 'required', 'order', 'is_active']
    list_filter = ['field_type', 'required', 'is_active', 'event']
    search_fields = ['label', 'field_name', 'event__title']


@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'ticket_type', 'position', 'status']
    list_filter = ['status', 'event']


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'registration', 'badge_type', 'is_printed']
    list_filter = ['badge_type', 'is_printed']


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ['registration', 'checked_in_by', 'check_in_time', 'method']
    list_filter = ['method', 'check_in_time']


@admin.register(AttendeePreference)
class AttendeePreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'networking_enabled']
    list_filter = ['event', 'networking_enabled']


@admin.register(AttendeeMessage)
class AttendeeMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'event', 'is_read', 'created_at']
    list_filter = ['is_read', 'event', 'created_at']
    search_fields = ['sender__email', 'recipient__email', 'subject']


@admin.register(SessionAttendance)
class SessionAttendanceAdmin(admin.ModelAdmin):
    list_display = ['registration', 'session', 'joined_at', 'rating']
    list_filter = ['session__event', 'rating']


@admin.register(RegistrationDocument)
class RegistrationDocumentAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'registration', 'field', 'file_size', 'is_validated', 'uploaded_at']
    list_filter = ['is_validated', 'uploaded_at', 'field__event']
    search_fields = ['original_filename', 'registration__registration_number']
    readonly_fields = ['file', 'original_filename', 'file_name', 'file_size', 'mime_type', 'uploaded_at']
    fieldsets = (
        ('Document Info', {
            'fields': ('registration', 'field', 'file')
        }),
        ('File Details', {
            'fields': ('original_filename', 'file_name', 'file_size', 'mime_type')
        }),
        ('Validation', {
            'fields': ('is_validated', 'validation_notes', 'validated_by', 'validated_at')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
