from dataclasses import dataclass


@dataclass(frozen=True)
class SlugMappingData:
    slug: str
    post_id: str
    timestamp: int
