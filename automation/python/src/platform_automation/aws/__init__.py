"""AWS package exports."""

from platform_automation.aws.discovery import AwsFacade
from platform_automation.aws.tags import ensure_tag, remove_tag

__all__ = ["AwsFacade", "ensure_tag", "remove_tag"]
