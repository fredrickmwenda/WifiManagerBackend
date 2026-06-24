import base64
import json
import requests
from datetime import datetime
from django.conf import settings


class MpesaClient:
    def __init__(self):
        self.env = settings.MPESA_ENVIRONMENT
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL
        self.transaction_type = settings.MPESA_TRANSACTION_TYPE
        
        self.base_url = (
            "https://sandbox.safaricom.co.ke"
            if self.env == "sandbox"
            else "https://api.safaricom.co.ke"
        )

    def _get_access_token(self) -> str:
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        credentials = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {credentials}"}
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _generate_password(self, timestamp: str) -> str:
        data = f"{self.shortcode}{self.passkey}{timestamp}"
        return base64.b64encode(data.encode()).decode()

    def stk_push(self, phone_number: str, amount: int, account_reference: str, transaction_desc: str) -> dict:
        """
        Initiate M-Pesa STK Push to user's phone.
        phone_number: 254712345678 format
        amount: KES amount
        """
        access_token = self._get_access_token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = self._generate_password(timestamp)

        # Clean phone number
        phone = phone_number.strip()
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif phone.startswith("+"):
            phone = phone[1:]

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": self.transaction_type,
            "Amount": amount,
            "PartyA": phone,
            "PartyB": self.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc,
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def query_stk_status(self, checkout_request_id: str) -> dict:
        """Query status of an STK push transaction."""
        access_token = self._get_access_token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = self._generate_password(timestamp)

        url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        return resp.json()