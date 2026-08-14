"""Mock SMS and KYC provider implementations."""

import logging
from typing import Any, Dict, Protocol

logger = logging.getLogger("bachnest.integrations")


class SMSProvider(Protocol):
    async def send_sms(self, phone_number: str, message: str) -> bool:
        ...


class MockSMSProvider:
    async def send_sms(self, phone_number: str, message: str) -> bool:
        logger.info(f"[MOCK SMS] Sent to {phone_number}: {message}")
        return True


class KYCProvider(Protocol):
    async def verify(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        ...


class MockKYCProvider:
    async def verify(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[MOCK KYC] Verified document: {document_data.get('document_number')}")
        return {
            "status": "APPROVED",
            "confidence_score": 0.98,
            "extracted_name": document_data.get("full_name", "Verified User"),
        }
