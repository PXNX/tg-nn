from dataclasses import dataclass
from typing import Optional


@dataclass
class Source:
    channel_id: int
    channel_name: str
    bias: str =""
    destination: Optional[str] = None
    display_name: Optional[str] = None
    invite: Optional[str] = None
    username: Optional[str] = None
    api_id: Optional[int] = None
    description: Optional[str] = None
    rating: Optional[int] = None
    detail_id: Optional[int] = None
    is_active: bool = False


@dataclass
class SourceDisplay:
    display_name: str
    bias: Optional[str] = None
    invite: Optional[str] = None
    username: Optional[str] = None
    detail_id: Optional[int] = None
    destination: Optional[int] = None


@dataclass
class Account:
    api_id: int
    api_hash: str
    name: str
    phone_number: str
    description: str


@dataclass
class Post:
    destination: int
    message_id: int
    source_channel_id: int
    source_message_id: int
    backup_id: int
    reply_id: Optional[int] = None
    message_text: Optional[str] = None
    file_id: Optional[str] = None
    footer:Optional[str] = None


@dataclass
class CrawlPost:
    caption: str
    texts: [str]
    image_urls: [str]
    video_urls: [str]
    url: str


@dataclass
class Destination:
    channel_id: int
    name: str
    group_id: Optional[int]
