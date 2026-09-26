"""Safe EC2 tag mutation with dry-run, confirm, and allowlist."""

from __future__ import annotations

from typing import Any

from platform_automation.aws.discovery import AwsFacade
from platform_automation.aws.session import client_for, safe_call
from platform_automation.errors import ValidationError
from platform_automation.validation import ALLOWED_TAG_MARKERS, require_confirm, require_resource_id


def _allowlisted(instance: dict[str, Any]) -> bool:
    tags = instance.get("tags") or {}
    haystack = " ".join([str(instance.get("instance_id")), *tags.keys(), *tags.values()]).lower()
    return any(marker in haystack for marker in ALLOWED_TAG_MARKERS)


def ensure_tag(
    facade: AwsFacade,
    resource_id: str,
    key: str,
    value: str,
    *,
    dry_run: bool = False,
    confirm: bool = False,
) -> dict[str, Any]:
    require_resource_id(resource_id)
    instances = {i["instance_id"]: i for i in facade.list_instances()}
    inst = instances.get(resource_id)
    if inst is None:
        raise ValidationError(f"instance not found or not visible: {resource_id}")
    if not _allowlisted(inst):
        raise ValidationError(
            "refusing tag mutation: resource not on automation-lab allowlist "
            f"(require tag/marker in {sorted(ALLOWED_TAG_MARKERS)})"
        )
    current = (inst.get("tags") or {}).get(key)
    if current == value:
        return {"resource_id": resource_id, "action": "unchanged", "key": key, "value": value}
    if dry_run:
        return {
            "resource_id": resource_id,
            "action": "would-create-or-update-tag",
            "key": key,
            "value": value,
            "previous": current,
        }
    require_confirm(confirm, "aws tag mutation")
    ec2 = client_for(facade.session, "ec2")
    safe_call(
        lambda: ec2.create_tags(Resources=[resource_id], Tags=[{"Key": key, "Value": value}])
    )
    return {"resource_id": resource_id, "action": "tagged", "key": key, "value": value}


def remove_tag(
    facade: AwsFacade,
    resource_id: str,
    key: str,
    *,
    dry_run: bool = False,
    confirm: bool = False,
) -> dict[str, Any]:
    require_resource_id(resource_id)
    instances = {i["instance_id"]: i for i in facade.list_instances()}
    inst = instances.get(resource_id)
    if inst is None:
        raise ValidationError(f"instance not found or not visible: {resource_id}")
    if not _allowlisted(inst):
        raise ValidationError("refusing tag removal: resource not on automation-lab allowlist")
    if key not in (inst.get("tags") or {}):
        return {"resource_id": resource_id, "action": "absent", "key": key}
    if dry_run:
        return {"resource_id": resource_id, "action": "would-remove-tag", "key": key}
    require_confirm(confirm, "aws tag removal")
    ec2 = client_for(facade.session, "ec2")
    safe_call(lambda: ec2.delete_tags(Resources=[resource_id], Tags=[{"Key": key}]))
    return {"resource_id": resource_id, "action": "untagged", "key": key}
