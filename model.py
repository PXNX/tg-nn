from dataclasses import dataclass
from typing import Optional


@dataclass
class Source:
    channel_id: int
    channel_name: str
    bias: Optional[str]
    display_name: Optional[str]
    invite: Optional[str]
    username: Optional[str]
    api_id: Optional[int]
    description: Optional[str]
    rating: Optional[int]
    detail_id: Optional[str]


@dataclass
class SourceDisplay:
    detail_id: int
    display_name: str
    bias: Optional[str]
    username: Optional[str]


@dataclass
class Account:
    api_id: int
    api_hash: str
    name: str
    phone_number: str
    description: str
