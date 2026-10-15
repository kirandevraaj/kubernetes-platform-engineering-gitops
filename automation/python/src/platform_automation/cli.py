"""CLI entrypoint for platform-automate."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from platform_automation import __version__
from platform_automation.config import load_settings
from platform_automation.controller import PlatformController
from platform_automation.doctor import run_doctor
from platform_automation.errors import AutomationError, CommandError, exit_code_for
from platform_automation.logging import setup_logging
from platform_automation.validation import require_confirm, require_namespace


def _print(data: Any) -> None:
    if isinstance(data, str):
        print(data)
    else:
        print(json.dumps(data, indent=2, default=str))


def _add_global(parser: argparse.ArgumentParser, *, nested: bool = False) -> None:
    """Register global flags.

    Nested copies use SUPPRESS defaults so a flag given after the subcommand
    (``kubernetes ensure --dry-run``) is honoured without overwriting one given
    before it (``--dry-run kubernetes ensure``).
    """

    def add(*flags: str, **kwargs: Any) -> None:
        if nested:
            kwargs["default"] = argparse.SUPPRESS
        try:
            parser.add_argument(*flags, **kwargs)
        except argparse.ArgumentError:
            # The subcommand defines its own option with this name (e.g. pods --namespace).
            pass

    add("--environment", choices=["vmware", "aws"])
    add("--cluster", choices=["ckad-lab", "platform-lab-aws"])
    add("--namespace", default=None)
    add("--region", default=None)
    add("--context", default=None)
    add("--aws-profile", default=None, dest="aws_profile")
    add("--config", default=None, dest="config_path")
    add("--timeout", type=float, default=None)
    add("--max-retries", type=int, default=None, dest="max_retries")
    add("--dry-run", action="store_true")
    add("--confirm", action="store_true")
    add("--verbose", action="store_true")
    add("--quiet", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="platform-automate", description="Platform automation CLI")
    _add_global(parser)
    sub = parser.add_subparsers(dest="command", required=True)
    leaves: list[argparse.ArgumentParser] = []

    def leaf(subparsers: Any, name: str, **kwargs: Any) -> argparse.ArgumentParser:
        command = subparsers.add_parser(name, **kwargs)
        leaves.append(command)
        return command

    leaf(sub, "version", help="Show package version")
    leaf(sub, "doctor", help="Check toolchain and connectivity")

    k = sub.add_parser("kubernetes", help="Kubernetes operations")
    k_sub = k.add_subparsers(dest="k_command", required=True)
    leaf(
        k_sub,
        "preflight",
        help="Read-only: bounded API reachability + namespace read check (no writes)",
    )
    leaf(k_sub, "nodes")
    leaf(k_sub, "namespaces")
    pods = leaf(k_sub, "pods")
    pods.add_argument("--namespace", default=None)
    ensure = leaf(k_sub, "ensure", help="Create/update the automation-lab demo stack (--confirm)")
    ensure.add_argument("--message", default="hello-automation")
    ensure.add_argument("--replicas", type=int, default=1)
    leaf(k_sub, "delete", help="Delete the automation-lab demo stack (--confirm)")
    wait = leaf(k_sub, "wait")
    wait.add_argument("--name", default="automation-demo")
    wait.add_argument("--namespace", default="automation-lab")

    a = sub.add_parser("aws", help="AWS operations")
    a_sub = a.add_subparsers(dest="a_command", required=True)
    for name in ("identity", "eks-info", "nodes", "vpcs", "subnets"):
        leaf(a_sub, name)
    tag = leaf(a_sub, "tag-resource")
    tag.add_argument("--resource-id", required=True)
    tag.add_argument("--key", required=True)
    tag.add_argument("--value", required=True)

    an = leaf(sub, "ansible", help="Run an Ansible playbook (--check, or --confirm to apply)")
    an.add_argument("--playbook", required=True)
    an.add_argument("--inventory", default=None)
    an.add_argument("--check", action="store_true")
    an.add_argument("--diff", action="store_true")

    p = sub.add_parser("platform", help="Capstone orchestration")
    p_sub = p.add_subparsers(dest="p_command", required=True)
    for name in ("inventory", "validate", "check", "plan", "apply", "verify", "reconcile"):
        leaf(p_sub, name)

    leaf(sub, "report", help="Emit last/local report summary")

    dr = sub.add_parser("dr", help="Disaster recovery helpers")
    dr_sub = dr.add_subparsers(dest="dr_command", required=True)
    leaf(dr_sub, "scenarios", help="List known DR scenarios")
    dr_verify = leaf(dr_sub, "verify", help="Read-only DR verification aggregate")
    dr_verify.add_argument("--kubernetes-api", choices=["pass", "fail", "unknown"], default="unknown")
    dr_verify.add_argument("--nodes", choices=["pass", "fail", "unknown"], default="unknown")
    dr_verify.add_argument("--argo", choices=["pass", "fail", "unknown"], default="unknown")
    dr_verify.add_argument("--applications", choices=["pass", "fail", "unknown"], default="unknown")
    dr_verify.add_argument("--pvc", choices=["pass", "fail", "unknown"], default="unknown")
    dr_verify.add_argument("--ebs", choices=["pass", "fail", "unknown"], default="unknown")
    dr_verify.add_argument("--observability", choices=["pass", "fail", "unknown"], default="unknown")
    dr_verify.add_argument("--application", choices=["pass", "fail", "unknown"], default="unknown")
    dr_report = leaf(dr_sub, "report", help="Emit DR report JSON + summary")
    dr_report.add_argument("--scenario", required=True)
    dr_report.add_argument("--failure-time", default=None)
    dr_report.add_argument("--recovery-time", default=None)
    dr_report.add_argument("--mechanism", default="")
    dr_report.add_argument("--result", default="UNKNOWN")
    dr_report.add_argument("--text", action="store_true", help="Also print human-readable summary")

    ops = sub.add_parser("ops", help="Read-only platform operations helpers")
    ops_sub = ops.add_subparsers(dest="ops_command", required=True)
    leaf(ops_sub, "health", help="Aggregate platform health (live read-only when cluster reachable)")
    ops_triage = leaf(ops_sub, "triage", help="Suggest triage layer from a symptom")
    ops_triage.add_argument("--symptom", required=True)
    ops_triage.add_argument("--layer", default=None)
    ops_report = leaf(ops_sub, "report", help="Emit ops report JSON/text")
    ops_report.add_argument("--text", action="store_true")
    ops_report.add_argument("--notes", default="")
    ops_evidence = leaf(ops_sub, "evidence", help="Write redacted local evidence bundle")
    _repo_root = Path(__file__).resolve().parents[4]
    ops_evidence.add_argument(
        "--output-dir",
        default=str(_repo_root / "automation" / "reports" / "evidence"),
        help="Directory for timestamped evidence (gitignored under automation/reports/)",
    )
    for command in leaves:
        _add_global(command, nested=True)
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

    return KubernetesFacade(context=settings.kube_context(), request_timeout=settings.timeout)


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
            if args.k_command == "ensure" and not settings.dry_run:
                require_confirm(settings.confirm, "kubernetes ensure")
            if args.k_command == "preflight":
                require_namespace(settings.namespace)
            facade = _k8s_facade(settings)
            if args.k_command == "preflight":
                payload = facade.preflight(settings.namespace)
                payload["context"] = settings.kube_context()
                _print(payload)
            elif args.k_command == "nodes":
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

            if not args.check:
                require_confirm(settings.confirm, "ansible playbook run without --check")
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
            dispatch: dict[str, Callable[[], Any]] = {
                "inventory": controller.discover,
                "validate": controller.validate,
                "check": controller.check,
                "plan": controller.plan,
                "apply": controller.apply,
                "verify": controller.verify,
                "reconcile": controller.reconcile,
            }
            result = dispatch[args.p_command]()
            _print(result)
            if args.p_command == "verify" and result.get("status") != "PASS":
                return CommandError.exit_code
            return 0

        if args.command == "report":
            controller = PlatformController(settings=settings)
            _print(controller.report())
            return 0

        if args.command == "dr":
            from platform_automation.dr import (
                build_dr_report,
                format_dr_report_text,
                list_scenarios,
                verify_platform,
            )

            def _tri(value: str) -> bool | None:
                if value == "pass":
                    return True
                if value == "fail":
                    return False
                return None

            if args.dr_command == "scenarios":
                _print(list_scenarios())
                return 0
            if args.dr_command == "verify":
                payload = verify_platform(
                    kubernetes_api_ok=_tri(args.kubernetes_api),
                    nodes_ready=_tri(args.nodes),
                    argo_healthy=_tri(args.argo),
                    applications_synced=_tri(args.applications),
                    pvc_bound=_tri(args.pvc),
                    ebs_attached=_tri(args.ebs),
                    observability_ok=_tri(args.observability),
                    application_healthy=_tri(args.application),
                )
                _print(payload)
                return 0 if payload["overall"] != "FAIL" else 4
            if args.dr_command == "report":
                payload = build_dr_report(
                    scenario=args.scenario,
                    failure_time=args.failure_time,
                    recovery_time=args.recovery_time,
                    recovery_mechanism=args.mechanism,
                    result=args.result,
                )
                if args.text:
                    print(format_dr_report_text(payload))
                else:
                    _print(payload)
                return 0

        if args.command == "ops":
            from platform_automation.ops import (
                build_ops_report,
                collect_evidence_bundle,
                collect_ops_health,
                format_ops_report_text,
                suggest_triage,
            )

            context = settings.context or settings.cluster or settings.environment or "unknown"

            if args.ops_command == "triage":
                _print(suggest_triage(args.symptom, layer=args.layer))
                return 0

            if args.ops_command == "health":
                try:
                    from platform_automation.ops.live import live_ops_health

                    facade = _k8s_facade(settings)
                    env = settings.environment or (
                        "aws" if "aws" in str(context) else "vmware"
                    )
                    payload = live_ops_health(facade, environment=env)
                except Exception:
                    payload = collect_ops_health()
                    payload["details"] = {
                        "note": "live cluster checks unavailable; returning UNKNOWN aggregate"
                    }
                _print(payload)
                return 0 if payload.get("overall") != "FAIL" else 4

            if args.ops_command == "report":
                health = None
                try:
                    from platform_automation.ops.live import live_ops_health

                    facade = _k8s_facade(settings)
                    env = settings.environment or (
                        "aws" if "aws" in str(context) else "vmware"
                    )
                    health = live_ops_health(facade, environment=env)
                except Exception:
                    health = collect_ops_health()
                payload = build_ops_report(
                    context=str(context), health=health, notes=args.notes
                )
                if args.text:
                    print(format_ops_report_text(payload))
                else:
                    _print(payload)
                return 0

            if args.ops_command == "evidence":
                collectors = None
                try:
                    from platform_automation.ops.live import live_evidence_collectors

                    facade = _k8s_facade(settings)
                    collectors = live_evidence_collectors(facade)
                except Exception:
                    collectors = None
                payload = collect_evidence_bundle(
                    output_dir=args.output_dir,
                    context=str(context),
                    collectors=collectors,
                    metadata={"environment": settings.environment, "cluster": settings.cluster},
                )
                _print(payload)
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
