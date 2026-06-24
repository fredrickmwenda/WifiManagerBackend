from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import SubscriptionPlan, Subscription, PaymentTransaction, Voucher, MPesaTransaction
from .serializers import (
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
    PaymentTransactionSerializer,
    VoucherSerializer,
    SubscriptionAnalyticsSerializer,
    MPesaTransactionSerializer,
    STKPushRequestSerializer,
    MPesaCallbackSerializer,
)
from utils.mpesa import MpesaClient
from apps.devices.models import Device


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'device', 'plan']


class PaymentTransactionViewSet(viewsets.ModelViewSet):
    queryset = PaymentTransaction.objects.all()
    serializer_class = PaymentTransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'channel', 'subscription__plan']
    search_fields = ['transaction_code', 'phone_number']


class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_used', 'plan']
    search_fields = ['code']

    @action(detail=False, methods=['post'], url_path='redeem')
    def redeem(self, request):
        code = request.data.get('code')
        device_id = request.data.get('device')
        if not code or not device_id:
            return Response({'detail': 'code and device required.'}, status=400)

        try:
            voucher = Voucher.objects.get(code=code.upper(), is_used=False)
            if voucher.expires_at and voucher.expires_at < timezone.now():
                return Response({'detail': 'Voucher expired.'}, status=400)

            device = Device.objects.get(id=device_id)
            sub = Subscription.objects.create(
                device=device,
                plan=voucher.plan,
                end_time=timezone.now() + timedelta(hours=voucher.plan.duration_hours),
                status='active'
            )
            voucher.is_used = True
            voucher.used_by = device
            voucher.used_at = timezone.now()
            voucher.save()

            PaymentTransaction.objects.create(
                subscription=sub,
                amount_ksh=0,
                channel='voucher',
                status='completed',
                paid_at=timezone.now(),
            )

            return Response({
                'detail': 'Voucher redeemed.',
                'subscription': SubscriptionSerializer(sub).data
            })
        except Voucher.DoesNotExist:
            return Response({'detail': 'Invalid or used voucher.'}, status=400)
        except Device.DoesNotExist:
            return Response({'detail': 'Device not found.'}, status=404)


class SubscriptionAnalyticsView(APIView):
    def get(self, request):
        today = timezone.now().date()
        total_revenue = PaymentTransaction.objects.filter(
            status='completed', paid_at__date=today
        ).aggregate(s=Sum('amount_ksh'))['s'] or 0

        active = Subscription.objects.filter(status='active').count()
        expired_today = Subscription.objects.filter(
            status='expired', end_time__date=today
        ).count()

        popular = Subscription.objects.values('plan__name').annotate(
            c=Count('id')
        ).order_by('-c').first()

        vouchers_redeemed = Voucher.objects.filter(
            is_used=True, used_at__date=today
        ).count()

        return Response({
            'total_revenue': total_revenue,
            'active_subscriptions': active,
            'expired_today': expired_today,
            'popular_plan': popular['plan__name'] if popular else 'None',
            'vouchers_redeemed': vouchers_redeemed,
        })


class MPesaPaymentViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate(self, request):
        serializer = STKPushRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone_number']
        plan_id = serializer.validated_data['plan_id']
        device_mac = serializer.validated_data['device_mac'].upper()

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({'detail': 'Invalid plan selected.'}, status=status.HTTP_400_BAD_REQUEST)

        tx = MPesaTransaction.objects.create(
            phone_number=phone,
            amount=plan.price_ksh,
            plan=plan,
            device_mac=device_mac,
            status='pending',
        )

        client = MpesaClient()
        try:
            resp = client.stk_push(
                phone_number=phone,
                amount=plan.price_ksh,
                account_reference=f"WIFI-{plan.name}",
                transaction_desc=f"WiFi access {plan.duration_hours}hrs",
            )

            tx.checkout_request_id = resp.get('CheckoutRequestID', '')
            tx.merchant_request_id = resp.get('MerchantRequestID', '')
            tx.status = 'processing'
            tx.save()

            return Response({
                'success': True,
                'checkout_request_id': tx.checkout_request_id,
                'merchant_request_id': tx.merchant_request_id,
                'message': 'Enter your M-Pesa PIN to complete payment.',
            })

        except Exception as e:
            tx.status = 'failed'
            tx.result_desc = str(e)
            tx.save()
            return Response({
                'success': False,
                'detail': 'Failed to initiate M-Pesa payment. Please try again.',
                'error': str(e),
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @action(detail=False, methods=['get'], url_path='status/(?P<checkout_id>[^/.]+)')
    def check_status(self, request, checkout_id=None):
        if not checkout_id:
            return Response({'detail': 'checkout_request_id required.'}, status=400)

        try:
            tx = MPesaTransaction.objects.get(checkout_request_id=checkout_id)
        except MPesaTransaction.DoesNotExist:
            return Response({'detail': 'Transaction not found.'}, status=404)

        if tx.status == 'processing':
            client = MpesaClient()
            try:
                result = client.query_stk_status(checkout_id)
                result_code = result.get('ResultCode', '1')
                if result_code == '0':
                    tx.status = 'completed'
                    tx.result_desc = result.get('ResultDesc', 'Success')
                    tx.save()
                    self._activate_subscription(tx)
                elif result_code:
                    tx.status = 'failed'
                    tx.result_desc = result.get('ResultDesc', 'Failed')
                    tx.save()
            except Exception:
                pass

        return Response({
            'status': tx.status,
            'receipt_number': tx.mpesa_receipt_number,
            'amount': tx.amount,
            'plan': tx.plan.name,
        })

    def _activate_subscription(self, tx: MPesaTransaction):
        # device, _ = Device.objects.get_or_create(
        #     mac_address=tx.device_mac,
        #     defaults={
        #         'name': f'Device {tx.device_mac}',
        #         'ip_address': '0.0.0.0',
        #         'status': 'connected',
        #         'device_type': 'phone',
        #     }
        # )

        # sub = Subscription.objects.create(
        #     device=device,
        #     plan=tx.plan,
        #     end_time=timezone.now() + timezone.timedelta(hours=tx.plan.duration_hours),
        #     status='active',
        # )

        # if device.status == 'blocked':
        #     device.status = 'connected'
        #     device.save()

        # PaymentTransaction.objects.create(
        #     subscription=sub,
        #     amount_ksh=tx.amount,
        #     channel='mpesa',
        #     transaction_code=tx.mpesa_receipt_number,
        #     status='completed',
        #     phone_number=tx.phone_number,
        #     paid_at=timezone.now(),
        # )

        """Create subscription and unblock device after successful payment."""
        # Find or create device
        device, created = Device.objects.get_or_create(
            mac_address=tx.device_mac,
            defaults={
                'name': f'Device {tx.device_mac}',
                'ip_address': '0.0.0.0',
                'status': 'connected',
                'device_type': 'phone',
            }
        )

        # CRITICAL: Save the M-Pesa phone number to the device for future WhatsApp alerts
        device.phone_number = tx.phone_number
        device.save(update_fields=['phone_number'])

        # Create subscription
        sub = Subscription.objects.create(
            device=device,
            plan=tx.plan,
            end_time=timezone.now() + timezone.timedelta(hours=tx.plan.duration_hours),
            status='active',
        )

        # Unblock if it was blocked
        if device.status == 'blocked':
            device.status = 'connected'
            device.save(update_fields=['status'])

        # Log payment
        PaymentTransaction.objects.create(
            subscription=sub,
            amount_ksh=tx.amount,
            channel='mpesa',
            transaction_code=tx.mpesa_receipt_number,
            status='completed',
            phone_number=tx.phone_number,
            paid_at=timezone.now(),
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_callback(request):
    serializer = MPesaCallbackSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'ResultCode': 1, 'ResultDesc': 'Invalid callback data'})

    body = serializer.validated_data.get('Body', {})
    stk_callback = body.get('stkCallback', {})

    result_code = stk_callback.get('ResultCode')
    checkout_request_id = stk_callback.get('CheckoutRequestID')
    result_desc = stk_callback.get('ResultDesc', '')

    try:
        tx = MPesaTransaction.objects.get(checkout_request_id=checkout_request_id)
    except MPesaTransaction.DoesNotExist:
        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    tx.raw_callback = body
    tx.result_code = str(result_code)
    tx.result_desc = result_desc

    if result_code == 0:
        callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
        metadata = {item.get('Name'): item.get('Value') for item in callback_metadata}

        tx.mpesa_receipt_number = metadata.get('MpesaReceiptNumber', '')
        tx.transaction_date = str(metadata.get('TransactionDate', ''))
        tx.status = 'completed'
        tx.save()

        view = MPesaPaymentViewSet()
        view._activate_subscription(tx)
    else:
        tx.status = 'failed'
        tx.save()

    return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})