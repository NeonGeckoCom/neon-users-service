from time import time
from typing import Dict, Any, List, Literal, Optional
from enum import IntEnum
from uuid import uuid4
from pydantic import BaseModel, Field
from datetime import date

class AccessRoles(IntEnum):
    NONE = 0
    GUEST = 1
    USER = 2
    ADMIN = 3
    OWNER = 4
    NODE = 5


class _UserConfig(BaseModel):
    first_name: str = ""
    middle_name: str = ""
    last_name: str = ""
    preferred_name: str = ""
    dob: Optional[date] = None
    email: str = ""
    avatar_url: str = ""
    about: str = ""
    phone: str = ""
    phone_verified: bool = False
    email_verified: bool = False


class _LanguageConfig(BaseModel):
    input_languages: List[str] = ["en-us"]
    output_languages: List[str] = ["en-us"]


class _UnitsConfig(BaseModel):
    time: Literal[12, 24] = 12
    date: Literal["MDY", "YMD", "YDM", "DMY"] = "MDY"
    measure: Literal["imperial", "metric"] = "imperial"


class _ResponseConfig(BaseModel):
    hesitation: bool = False
    limit_dialog: bool = False
    tts_gender: Literal["male", "female"] = "female"
    tts_speed_multiplier: float = 1.0


class _LocationConfig(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    name: Optional[str] = None
    timezone: Optional[str] = None


class _PrivacyConfig(BaseModel):
    save_text: bool = True
    save_audio: bool = False


class NeonUserConfig(BaseModel):
    """
    Defines user configuration used in Neon Core.
    """
    skills: Dict[str, Dict[str, Any]] = {}
    user: _UserConfig = _UserConfig()
    # Former `speech` schema is replaced by `language` which is a more general
    # format.
    language: _LanguageConfig = _LanguageConfig()
    units: _UnitsConfig = _UnitsConfig()
    # Former `location` schema is replaced here with a minimal spec from which
    # the remaining values may be calculated
    location: _LocationConfig = _LocationConfig()
    response_mode: _ResponseConfig = _ResponseConfig()
    privacy: _PrivacyConfig = _PrivacyConfig()


class KlatConfig(BaseModel):
    """
    Defines user configuration used in PyKlatChat.
    """
    is_tmp: bool = True
    preferences: Dict[str, Any] = {}


class BrainForgeConfig(BaseModel):
    """
    Defines configuration used in BrainForge LLM applications.
    """
    inference_access: Dict[str, Dict[str, List[str]]] = {}


class PermissionsConfig(BaseModel):
    """
    Defines roles for supported projects/service families.
    """
    klat: AccessRoles = AccessRoles.NONE
    core: AccessRoles = AccessRoles.NONE
    diana: AccessRoles = AccessRoles.NONE
    node: AccessRoles = AccessRoles.NONE
    hub: AccessRoles = AccessRoles.NONE
    llm: AccessRoles = AccessRoles.NONE


class TokenConfig(BaseModel):
    description: str
    client_id: str
    expiration_timestamp: int
    refresh_token: str
    last_used_timestamp: int


class User(BaseModel):
    username: str
    password_hash: str
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    created_timestamp: int = Field(default_factory=lambda: round(time()))
    neon: NeonUserConfig = NeonUserConfig()
    klat: KlatConfig = KlatConfig()
    llm: BrainForgeConfig = BrainForgeConfig()
    permissions: PermissionsConfig = PermissionsConfig()
    tokens: List[TokenConfig] = []

    def __eq__(self, other):
        return self.model_dump() == other.model_dump()
