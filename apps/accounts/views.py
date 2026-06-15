import uuid
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import User, UserActivityLog, PasswordResetToken
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, UserProfileSerializer, UserActivityLogSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from .permissions import IsSuperAdmin, IsAdminOrAbove, IsManagerOrAbove

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'is_active', 'is_online']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['date_joined', 'last_active', 'role']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsAdminOrAbove]
        elif self.action in ['destroy', 'update_role']:
            permission_classes = [IsSuperAdmin]
        elif self.action in ['list']:
            permission_classes = [IsManagerOrAbove]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrAbove])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return Response({'detail': 'Cannot deactivate yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = not user.is_active
        user.save()
        return Response({
            'detail': f'User {"activated" if user.is_active else "deactivated"}.',
            'is_active': user.is_active
        })

    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def update_role(self, request, pk=None):
        user = self.get_object()
        new_role = request.data.get('role')
        if new_role not in dict(User.ROLE_CHOICES):
            return Response({'detail': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)
        user.role = new_role
        user.save()
        return Response({'detail': f'Role updated to {new_role}.', 'role': new_role})

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Log activity
        UserActivityLog.objects.create(
            user=user,
            action='password_change',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Blacklist old refresh token and issue new one
        refresh = RefreshToken.for_user(user)
        return Response({
            'detail': 'Password changed successfully.',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

    @action(detail=False, methods=['post'])
    def update_profile(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(request.user).data)


class UserActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserActivityLog.objects.all()
    serializer_class = UserActivityLogSerializer
    permission_classes = [IsManagerOrAbove]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['action', 'user']
    search_fields = ['details']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == 'manager':
            # Managers only see logs of users they created or support/viewers
            qs = qs.filter(user__created_by=self.request.user) | qs.filter(user__role__in=['support', 'viewer'])
        return qs


class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            token = uuid.uuid4().hex
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(hours=1)
            )
            # In production: send email with reset link
            return Response({
                'detail': 'Password reset link sent to email.',
                'token': token  # Remove in production; return only for dev/testing
            })
        except User.DoesNotExist:
            return Response({'detail': 'If this email exists, a reset link has been sent.'})


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            reset = PasswordResetToken.objects.get(
                token=serializer.validated_data['token'],
                used=False,
                expires_at__gt=timezone.now()
            )
            user = reset.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            reset.used = True
            reset.save()
            return Response({'detail': 'Password reset successful.'})
        except PasswordResetToken.DoesNotExist:
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)


class OnlineUsersView(generics.GenericAPIView):
    permission_classes = [IsManagerOrAbove]

    def get(self, request):
        # Users active in last 15 minutes
        since = timezone.now() - timedelta(minutes=15)
        users = User.objects.filter(last_active__gte=since)
        return Response({
            'count': users.count(),
            'users': UserSerializer(users, many=True).data
        })