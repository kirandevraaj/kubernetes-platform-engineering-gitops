"""CLI entrypoint for platform-automate."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from platform_automation import __version__
from platform_automation.config import load_settings
from platform_automation.controller import PlatformController
from platform_automation.doctor import run_doctor
from platform_automation.errors import AutomationError, exit_code_for
from platform_automation.logging import setup_logging


def _print(data: Any) -> None:
    if isinstance(data, str):
        print(data)
    else:
        print(json.dumps(data, indent=2, default=str))


def _add_global(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--environment", choices=["vmware", "aws"])
    parser.add_argument("--cluster", choices=["ckad-lab", "platform-lab-aws"])
    parser.add_argument("--namespace", default=None)
    parser.add_argument("--region", default=None)
    parser.add_argument("--context", default=None)
    parser.add_argument("--aws-profile", default=None, dest="aws_profile")
    parser.add_argument("--config", default=None, dest="config_path")
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--max-retries", type=int, default=None, dest="max_retries")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--quiet", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="platform-automate", description="Platform automation CLI")
    _add_global(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="Show package version")
    sub.add_parser("doctor", help="Check toolchain and connectivity")

    k = sub.add_parser("kubernetes", help="Kubernetes operations")
    k_sub = k.add_subparsers(dest="k_command", required=True)
    k_sub.add_parser("nodes")
    k_sub.add_parser("namespaces")
    pods = k_sub.add_parser("pods")
    pods.add_argument("--namespace", default=None)
    ensure = k_sub.add_parser("ensure")
    ensure.add_argument("--message", default="hello-automation")
    ensure.add_argument("--replicas", type=int, default=1)
    k_sub.add_parser("delete")
    wait = k_sub.add_parser("wait")
    wait.add_argument("--name", default="automation-demo")
    wait.add_argument("--namespace", default="automation-lab")

    a = sub.add_parser("aws", help="AWS operations")
    a_sub = a.add_subparsers(dest="a_command", required=True)
    for name in ("identity", "eks-info", "nodes", "vpcs", "subnets"):
        a_sub.add_parser(name)
    tag = a_sub.add_parser("tag-resource")
    tag.add_argument("--resource-id", required=True)
    tag.add_argument("--key", required=True)
    tag.add_argument("--value", required=True)

    an = sub.add_parser("ansible", help="Run an Ansible playbook")
    an.add_argument("--playbook", required=True)
    an.add_argument("--inventory", default=None)
    an.add_argument("--check", action="store_true")
    an.add_argument("--diff", action="store_true")

    p = sub.add_parser("platform", help="Capstone orchestration")
    p_sub = p.add_subparsers(dest="p_command", required=True)
    for name in ("inventory", "validate", "check", "plan", "apply", "verify", "reconcile"):
        p_sub.add_parser(name)

    sub.add_parser("report", help="Emit last/local report summary")
    return parser


def _settings_from_args(args: argparse.Namespace):
    overrides = {
        "environment": args.environment,
        "cluster": args.cluster,
        "namespace": args.namespace,
        "region": args.region,
        "context": args.context,
        "aws_profile": args.aws_profile,
        "timeout": args.timeout,
        "max_retries": args.max_retries,
        "dry_run": args.dry_run or None,
        "confirm": args.confirm or None,
        "verbose": args.verbose or None,
        "quiet": args.quiet or None,
    }
    # dry_run/confirm are bools — only pass if set
    cleaned = {}
    for key, value in overrides.items():
        if value is None:
            continue
        if key in {"dry_run", "confirm", "verbose", "quiet"} and value is False:
            continue
        cleaned[key] = value
    return load_settings(config_path=args.config_path, cli_overrides=cleaned)


def _k8s_facade(settings):
    from platform_automation.kubernetes.client import KubernetesFacade

    return KubernetesFacade(context=settings.kube_context())


def _aws_facade(settings):
    from platform_automation.aws import AwsFacade

    return AwsFacade(profile=settings.aws_profile, region=settings.region)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = _settings_from_args(args)
        setup_logging(verbose=settings.verbose, quiet=settings.quiet)

        if args.command == "version":
            _print({"version": __version__})
            return 0

        if args.command == "doctor":
            _print(run_doctor(settings))
            return 0

        if args.command == "kubernetes":
            facade = _k8s_facade(settings)
            if args.k_command == "nodes":
                _print(facade.list_nodes())
            elif args.k_command == "namespaces":
                _print(facade.list_namespaces())
            elif args.k_command == "pods":
                ns = args.namespace or settings.namespace
                _print(facade.list_pods(ns))
            elif args.k_command == "ensure":
                from platform_automation.kubernetes.idempotent import ensure_demo_stack

                _print(
                    ensure_demo_stack(
                        facade,
                        message=args.message,
                        replicas=args.replicas,
                        dry_run=settings.dry_run,
                    )
                )
            elif args.k_command == "delete":
                from platform_automation.kubernetes.idempotent import delete_demo_stack

                _print(
                    delete_demo_stack(
                        facade, confirm=settings.confirm, dry_run=settings.dry_run
                    )
                )
            elif args.k_command == "wait":
                from platform_automation.kubernetes.wait import wait_for_deployment_ready

                _print(
                    wait_for_deployment_ready(
                        facade,
                        args.namespace or "automation-lab",
                        args.name,
                        timeout=settings.timeout,
                    )
                )
            return 0

        if args.command == "aws":
            aws = _aws_facade(settings)
            if args.a_command == "identity":
                _print(aws.identity())
            elif args.a_command == "eks-info":
                _print(aws.describe_eks())
            elif args.a_command == "nodes":
                _print(aws.list_instances())
            elif args.a_command == "vpcs":
                _print(aws.describe_vpcs())
            elif args.a_command == "subnets":
                _print(aws.describe_subnets())
            elif args.a_command == "tag-resource":
                from platform_automation.aws import ensure_tag

                _print(
                    ensure_tag(
                        aws,
                        args.resource_id,
                        args.key,
                        args.value,
                        dry_run=settings.dry_run,
                        confirm=settings.confirm,
                    )
                )
            return 0

        if args.command == "ansible":
            from platform_automation.ansible import run_playbook

            result = run_playbook(
                args.playbook,
                inventory=args.inventory,
                timeout=settings.timeout,
                check=args.check,
                diff=args.diff,
            )
            _print(
                {
                    "rc": result.rc,
                    "status": result.status,
                    "backend": result.backend,
                    "duration": result.duration,
                }
            )
            return 0 if result.ok else 4

        if args.command == "platform":
            k8s = _k8s_facade(settings)
            aws = None
            if settings.environment == "aws":
                try:
                    aws = _aws_facade(settings)
                except Exception:
                    aws = None
            controller = PlatformController(settings=settings, k8s=k8s, aws=aws)
            dispatch = {
                "inventory": controller.discover,
                "validate": controller.validate,
                "check": controller.check,
                "plan": controller.plan,
                "apply": controller.apply,
                "verify": controller.verify,
                "reconcile": controller.reconcile,
            }
            _print(dispatch[args.p_command]())
            return 0

        if args.command == "report":
            controller = PlatformController(settings=settings)
            _print(controller.report())
            return 0

        parser.error(f"unknown command {args.command}")
        return 2
    except AutomationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exit_code_for(exc)
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
