#!/usr/bin/env python3
"""Small, dependency-free adb helper for safe Android notification cleanup."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BACKUP_ROOT = ROOT / "backups"
PROMO_RE = re.compile(r"广告|营销|内容与营销|推荐|热点|热门|资讯|福利|活动|优惠|推广|热搜")
KEEP_RE = re.compile(r"聊天|私信|消息|邮件|订单|物流|支付|交易|安全|账户|账号|日历|天气|预警|更新|升级|AI|任务|提醒|导航|音乐|播放")
PROPS = (
    "ro.product.brand",
    "ro.product.manufacturer",
    "ro.product.model",
    "ro.vendor.oplus.market.name",
    "ro.build.version.release",
    "ro.build.version.sdk",
    "ro.build.version.security_patch",
    "ro.build.display.id",
    "ro.build.version.oplusrom",
)


def adb(*args: str, serial: str | None = None, check: bool = True) -> str:
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    cmd += list(args)
    result = subprocess.run(cmd, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if check and result.returncode:
        raise RuntimeError(f"adb failed ({result.returncode}): {' '.join(cmd)}\n{result.stderr.strip()}")
    return result.stdout


def devices() -> list[dict[str, str]]:
    rows = []
    for line in adb("devices", "-l").splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 2:
            rows.append({"serial": fields[0], "state": fields[1], "details": " ".join(fields[2:])})
    return rows


def one_device(serial: str | None) -> str:
    if serial:
        return serial
    found = [d for d in devices() if d["state"] == "device"]
    if len(found) != 1:
        raise RuntimeError("Expected exactly one authorized adb device; use --serial when more than one is connected.")
    return found[0]["serial"]


def settings(serial: str, namespace: str, names: list[str]) -> dict[str, str]:
    return {name: adb("shell", "settings", "get", namespace, name, serial=serial).strip() for name in names}


def parse_channels(dump: str) -> list[dict[str, object]]:
    current = ""
    in_prefs = False
    channels = []
    for line in dump.splitlines():
        if re.match(r"^\s*PackagePreferences:", line):
            in_prefs = True
            continue
        if not in_prefs:
            continue
        app = re.search(r"^\s*AppSettings:\s+(\S+)", line)
        if app:
            current = app.group(1)
            continue
        channel = re.search(
            r"NotificationChannel\{mId='([^']+)',\s*mName=([^,]+).*?mImportance=(-?\d+).*?mDeleted=(true|false)",
            line,
        )
        if channel and current:
            name = channel.group(2).strip()
            protected = bool(KEEP_RE.search(name) or KEEP_RE.search(channel.group(1)))
            candidate = bool(PROMO_RE.search(name) or PROMO_RE.search(channel.group(1))) and not protected
            channels.append(
                {
                    "package": current,
                    "id": channel.group(1),
                    "name": name,
                    "importance": int(channel.group(3)),
                    "deleted": channel.group(4) == "true",
                    "candidate": candidate,
                }
            )
    return channels


def inspect(serial: str) -> dict[str, object]:
    props = {name: adb("shell", "getprop", name, serial=serial).strip() for name in PROPS}
    disabled = [x.removeprefix("package:") for x in adb("shell", "pm", "list", "packages", "-d", serial=serial).splitlines()]
    packages = [x.removeprefix("package:") for x in adb("shell", "pm", "list", "packages", "-3", serial=serial).splitlines()]
    channels = parse_channels(adb("shell", "dumpsys", "notification", serial=serial))
    return {
        "serial": serial,
        "properties": props,
        "third_party_packages": packages,
        "disabled_packages": disabled,
        "channels": channels,
        "settings": {
            "global": settings(
                serial,
                "global",
                ["network_recommendations_enabled", "recommend_info_update_interval", "recommend_notify_interval"],
            ),
            "secure": settings(
                serial,
                "secure",
                ["personalized_clicked", "operation_manual_recommended_settings", "lock_screen_show_notifications"],
            ),
        },
    }


def backup(serial: str) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BACKUP_ROOT / stamp
    path.mkdir(parents=True, exist_ok=False)
    data = inspect(serial)
    (path / "state.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (path / "notification-dump.txt").write_text(adb("shell", "dumpsys", "notification", serial=serial), encoding="utf-8")
    return path


def candidates(data: dict[str, object]) -> list[dict[str, object]]:
    return [c for c in data["channels"] if c["candidate"] and not c["deleted"] and c["importance"] > 0]


def toggle_channel(serial: str, package: str, channel_id: str, enable: bool) -> None:
    adb(
        "shell",
        "am",
        "force-stop",
        "com.oplus.notificationmanager",
        serial=serial,
    )
    adb(
        "shell",
        "am",
        "start",
        "-a",
        "android.settings.CHANNEL_NOTIFICATION_SETTINGS",
        "--es",
        "android.provider.extra.APP_PACKAGE",
        package,
        "--es",
        "android.provider.extra.CHANNEL_ID",
        channel_id,
        serial=serial,
    )
    time.sleep(1.5)
    adb("shell", "input", "keyevent", "KEYCODE_WAKEUP", serial=serial, check=False)
    ui_path = "/data/local/tmp/android_ad_optimizer.xml"
    adb("shell", "uiautomator", "dump", ui_path, serial=serial)
    xml = adb("shell", "cat", ui_path, serial=serial)
    switch = re.search(
        r'<node[^>]+resource-id="android:id/switch_widget"[^>]+checked="(true|false)"[^>]+bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
        xml,
    )
    if 'text="允许通知"' not in xml or not switch:
        raise RuntimeError("Notification settings page did not expose a verifiable switch.")
    current = switch.group(1) == "true"
    if current == enable:
        return
    x = (int(switch.group(2)) + int(switch.group(4))) // 2
    y = (int(switch.group(3)) + int(switch.group(5))) // 2
    adb("shell", "input", "tap", str(x), str(y), serial=serial)
    time.sleep(0.8)
    after = adb("shell", "dumpsys", "notification", serial=serial)
    states = [c for c in parse_channels(after) if c["package"] == package and c["id"] == channel_id]
    if not states or (states[0]["importance"] > 0) != enable:
        raise RuntimeError(f"Could not verify channel change for {package}:{channel_id}")


def apply_changes(serial: str, yes: bool) -> None:
    data = inspect(serial)
    selected = candidates(data)
    if not yes:
        raise RuntimeError("This command changes notification settings. Review `plan` and rerun with --yes.")
    for channel in selected:
        toggle_channel(serial, str(channel["package"]), str(channel["id"]), False)
        print(f"disabled: {channel['package']} / {channel['name']} ({channel['id']})")


def restore(serial: str, backup_path: Path) -> None:
    data = json.loads((backup_path / "state.json").read_text(encoding="utf-8"))
    original = {
        (c["package"], c["id"]): c
        for c in data["channels"]
        if not c["deleted"] and c["importance"] > 0
    }
    current = parse_channels(adb("shell", "dumpsys", "notification", serial=serial))
    for channel in current:
        key = (channel["package"], channel["id"])
        if key in original and channel["importance"] == 0:
            toggle_channel(serial, channel["package"], channel["id"], True)
            print(f"restored: {channel['package']} / {channel['name']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("devices")
    sub.add_parser("inspect")
    sub.add_parser("plan")
    sub.add_parser("backup")
    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("--yes", action="store_true")
    restore_parser = sub.add_parser("restore")
    restore_parser.add_argument("path", type=Path)
    restore_parser.add_argument("--yes", action="store_true")
    sub.add_parser("finish")
    args = parser.parse_args()
    if args.command == "devices":
        print(json.dumps(devices(), ensure_ascii=False, indent=2))
        return 0
    serial = one_device(args.serial)
    if args.command == "inspect":
        print(json.dumps(inspect(serial), ensure_ascii=False, indent=2))
    elif args.command == "plan":
        print(json.dumps(candidates(inspect(serial)), ensure_ascii=False, indent=2))
    elif args.command == "backup":
        print(backup(serial))
    elif args.command == "apply":
        apply_changes(serial, args.yes)
    elif args.command == "restore":
        if not args.yes:
            raise RuntimeError("Restoring notification settings changes device state; rerun with --yes.")
        restore(serial, args.path)
    elif args.command == "finish":
        print("USB debugging remains enabled. Turn it off manually in Developer options when finished.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
