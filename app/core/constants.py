"""Domain constants, Enums, and SLA configurations for BachNest."""

from enum import Enum


class UserRole(str, Enum):
    BACHELOR = "BACHELOR"
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class KYCStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class KYCDocumentType(str, Enum):
    NID = "NID"
    PASSPORT = "PASSPORT"
    BIRTH_CERTIFICATE = "BIRTH_CERTIFICATE"
    STUDENT_ID = "STUDENT_ID"
    EMPLOYEE_ID = "EMPLOYEE_ID"


class PropertyType(str, Enum):
    FLAT = "FLAT"
    SUBLET = "SUBLET"
    MESS = "MESS"
    HOSTEL = "HOSTEL"


class RoomType(str, Enum):
    SINGLE = "SINGLE"
    MASTER = "MASTER"
    SHARED = "SHARED"


class BookingStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED_BY_OWNER = "APPROVED_BY_OWNER"
    REJECTED = "REJECTED"
    DEPOSIT_PAID = "DEPOSIT_PAID"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TenancyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    NOTICE_SERVED = "NOTICE_SERVED"
    TERMINATED = "TERMINATED"
    EVICTED = "EVICTED"


class AgreementStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_SIGNATURE = "PENDING_SIGNATURE"
    SIGNED = "SIGNED"
    EXPIRED = "EXPIRED"


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, Enum):
    MOCK = "MOCK"
    BKASH = "BKASH"
    NAGAD = "NAGAD"
    ROCKET = "ROCKET"
    SSLCOMMERZ = "SSLCOMMERZ"
    BANK_TRANSFER = "BANK_TRANSFER"
    CASH = "CASH"


class ComplaintCategory(str, Enum):
    PLUMBING = "PLUMBING"
    ELECTRICAL = "ELECTRICAL"
    APPLIANCE = "APPLIANCE"
    STRUCTURAL = "STRUCTURAL"
    INTERNET = "INTERNET"
    SECURITY = "SECURITY"
    NOISE = "NOISE"
    CLEANLINESS = "CLEANLINESS"
    OTHER = "OTHER"


class ComplaintPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EMERGENCY = "EMERGENCY"


class ComplaintStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class NoticePriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class EmergencyType(str, Enum):
    SECURITY_INTRUDER = "SECURITY_INTRUDER"
    MEDICAL = "MEDICAL"
    FIRE = "FIRE"
    HARASSMENT = "HARASSMENT"
    ACCIDENT = "ACCIDENT"
    OTHER = "OTHER"


class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class AuditAction(str, Enum):
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    KYC_SUBMITTED = "KYC_SUBMITTED"
    KYC_APPROVED = "KYC_APPROVED"
    KYC_REJECTED = "KYC_REJECTED"
    PROPERTY_CREATED = "PROPERTY_CREATED"
    PROPERTY_UPDATED = "PROPERTY_UPDATED"
    PROPERTY_PUBLISHED = "PROPERTY_PUBLISHED"
    BOOKING_CREATED = "BOOKING_CREATED"
    BOOKING_APPROVED = "BOOKING_APPROVED"
    BOOKING_REJECTED = "BOOKING_REJECTED"
    TENANCY_CREATED = "TENANCY_CREATED"
    INVOICE_CREATED = "INVOICE_CREATED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    COMPLAINT_CREATED = "COMPLAINT_CREATED"
    COMPLAINT_STATUS_CHANGED = "COMPLAINT_STATUS_CHANGED"
    SOS_TRIGGERED = "SOS_TRIGGERED"
    SOS_RESOLVED = "SOS_RESOLVED"
    ADMIN_ACTION = "ADMIN_ACTION"


# SLA Deadlines in Hours for Complaints
SLA_HOURS_MAP = {
    ComplaintPriority.LOW: 72,
    ComplaintPriority.MEDIUM: 48,
    ComplaintPriority.HIGH: 24,
    ComplaintPriority.EMERGENCY: 2,
}
