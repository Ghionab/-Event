from rest_framework import permissions


class IsOrganizer(permissions.BasePermission):
    """
    Organizers can access their own events and resources
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['organizer', 'admin']
        )


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


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Read access for all authenticated users, write only for organizers
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['organizer', 'admin']
        )


class IsEventOrganizer(permissions.BasePermission):
    """
    Check if user is the organizer of a specific event
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'event'):
            obj = obj.event
        return obj.organizer == request.user or request.user.role == 'admin'


class IsEventOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow event owner full access, others read-only
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.organizer == request.user or request.user.role == 'admin'


class IsPublicEventOrReadOnly(permissions.BasePermission):
    """
    Allow public read access to events, write only for authenticated organizers
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['organizer', 'admin']
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.organizer == request.user or request.user.role == 'admin'


class IsAdmin(permissions.BasePermission):
    """
    Admin only access
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'
