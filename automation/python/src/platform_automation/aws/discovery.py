"""AWS identity and read-only discovery with pagination."""

from __future__ import annotations

from typing import Any

from platform_automation.aws.session import build_session, client_for, safe_call


class AwsFacade:
    def __init__(self, *, profile: str | None = None, region: str | None = None) -> None:
        self.session = build_session(profile=profile, region=region)
        self.region = region or self.session.region_name or "us-east-1"

    def identity(self) -> dict[str, Any]:
        sts = client_for(self.session, "sts")
        return safe_call(lambda: sts.get_caller_identity())

    def list_instances(self) -> list[dict[str, Any]]:
        ec2 = client_for(self.session, "ec2")
        paginator = ec2.get_paginator("describe_instances")
        out: list[dict[str, Any]] = []

        def _page():
            for page in paginator.paginate():
                for reservation in page.get("Reservations", []):
                    for inst in reservation.get("Instances", []):
                        tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
                        out.append(
                            {
                                "instance_id": inst.get("InstanceId"),
                                "state": inst.get("State", {}).get("Name"),
                                "type": inst.get("InstanceType"),
                                "az": inst.get("Placement", {}).get("AvailabilityZone"),
                                "private_ip": inst.get("PrivateIpAddress"),
                                "tags": tags,
                            }
                        )
            return out

        return safe_call(_page)

    def describe_vpcs(self) -> list[dict[str, Any]]:
        ec2 = client_for(self.session, "ec2")
        paginator = ec2.get_paginator("describe_vpcs")

        def _page():
            items = []
            for page in paginator.paginate():
                for vpc in page.get("Vpcs", []):
                    items.append(
                        {
                            "vpc_id": vpc.get("VpcId"),
                            "cidr": vpc.get("CidrBlock"),
                            "is_default": vpc.get("IsDefault"),
                            "state": vpc.get("State"),
                        }
                    )
            return items

        return safe_call(_page)

    def describe_subnets(self) -> list[dict[str, Any]]:
        ec2 = client_for(self.session, "ec2")
        paginator = ec2.get_paginator("describe_subnets")

        def _page():
            items = []
            for page in paginator.paginate():
                for subnet in page.get("Subnets", []):
                    items.append(
                        {
                            "subnet_id": subnet.get("SubnetId"),
                            "vpc_id": subnet.get("VpcId"),
                            "az": subnet.get("AvailabilityZone"),
                            "cidr": subnet.get("CidrBlock"),
                            "map_public_ip": subnet.get("MapPublicIpOnLaunch"),
                        }
                    )
            return items

        return safe_call(_page)

    def describe_eks(self, cluster_name: str | None = None) -> list[dict[str, Any]]:
        eks = client_for(self.session, "eks")

        def _run():
            names = [cluster_name] if cluster_name else eks.list_clusters().get("clusters", [])
            # list_clusters is paginated
            if not cluster_name:
                names = []
                paginator = eks.get_paginator("list_clusters")
                for page in paginator.paginate():
                    names.extend(page.get("clusters", []))
            details = []
            for name in names:
                desc = eks.describe_cluster(name=name)["cluster"]
                details.append(
                    {
                        "name": desc.get("name"),
                        "status": desc.get("status"),
                        "version": desc.get("version"),
                        "endpoint": desc.get("endpoint"),
                        "arn": desc.get("arn"),
                    }
                )
            return details

        return safe_call(_run)

    def list_addons(self, cluster_name: str) -> list[dict[str, Any]]:
        eks = client_for(self.session, "eks")

        def _run():
            addons = []
            paginator = eks.get_paginator("list_addons")
            for page in paginator.paginate(clusterName=cluster_name):
                for addon in page.get("addons", []):
                    detail = eks.describe_addon(clusterName=cluster_name, addonName=addon)["addon"]
                    addons.append(
                        {
                            "name": detail.get("addonName"),
                            "version": detail.get("addonVersion"),
                            "status": detail.get("status"),
                        }
                    )
            return addons

        return safe_call(_run)
