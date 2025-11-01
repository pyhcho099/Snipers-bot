from enum import Enum

class ContractRole(str, Enum):
    RP = 'rp'
    TL = 'tl'
    PR = 'pr'
    CLRD = 'clrd'
    TS = 'ts'
    QC = 'qc'
    UPLOADER = 'uploader'

class TransactionType(str, Enum):
    EARN = 'earn'
    SPEND = 'spend'
    TRANSFER = 'transfer'
    PENALTY = 'penalty'
    REFUND = 'refund'

class BountyStatus(str, Enum):
    OPEN = 'open'
    CLAIMED = 'claimed'
    RESOLVED = 'resolved'
    CANCELLED = 'cancelled'
