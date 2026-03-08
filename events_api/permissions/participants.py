from rest_framework import permissions


class IsParticipant(permissions.BasePermission):
    """
    Participants can register for events and view their registrations
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['attendee', 'organizer', 'admin']
        )


class IsRegistrationOwner(permissions.BasePermission):
    """
    User can only access their own registrations
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.role == 'admin'


class CanRegisterForEvent(permissions.BasePermission):
    """
    Check if user can register for an event
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['attendee', 'organizer', 'admin']
