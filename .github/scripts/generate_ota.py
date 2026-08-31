#!/usr/bin/env python3
"""Generate a GitHub Pages site for installing the latest signed IPA over the air."""

from __future__ import annotations

import argparse
import html
import json
import os
import plistlib
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


def fetch_json(url: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "PiliPlus-iOS-Build",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as response:
        return json.load(response)


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "PiliPlus-iOS-Build"},
    )
    with urllib.request.urlopen(request) as response, destination.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)


def read_app_metadata(ipa_path: Path) -> dict[str, str]:
    with zipfile.ZipFile(ipa_path) as archive:
        info_paths = [
            name
            for name in archive.namelist()
            if name.startswith("Payload/")
            and name.count("/") == 2
            and name.endswith(".app/Info.plist")
        ]
        if len(info_paths) != 1:
            raise RuntimeError(f"Expected one application Info.plist, found {len(info_paths)}")
        metadata = plistlib.loads(archive.read(info_paths[0]))

    required = {
        "bundle_id": metadata.get("CFBundleIdentifier"),
        "bundle_version": metadata.get("CFBundleVersion"),
        "short_version": metadata.get("CFBundleShortVersionString"),
        "display_name": metadata.get("CFBundleDisplayName")
        or metadata.get("CFBundleName")
        or "PiliPlus",
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Missing IPA metadata: {', '.join(missing)}")
    return {name: str(value) for name, value in required.items()}


def write_site(output: Path, site_url: str, release: dict, asset: dict, app: dict[str, str]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    site_url = site_url.rstrip("/")
    manifest_url = f"{site_url}/manifest.plist?v={urllib.parse.quote(str(release['tag_name']))}"
    install_url = "itms-services://?action=download-manifest&url=" + urllib.parse.quote(
        manifest_url, safe=""
    )

    manifest = {
        "items": [
            {
                "assets": [
                    {
                        "kind": "software-package",
                        "url": asset["browser_download_url"],
                    }
                ],
                "metadata": {
                    "bundle-identifier": app["bundle_id"],
                    "bundle-version": app["bundle_version"],
                    "kind": "software",
                    "title": app["display_name"],
                },
            }
        ]
    }
    (output / "manifest.plist").write_bytes(
        plistlib.dumps(manifest, fmt=plistlib.FMT_XML, sort_keys=False)
    )

    latest = {
        "release_tag": release["tag_name"],
        "release_name": release.get("name") or release["tag_name"],
        "app_version": app["short_version"],
        "build_number": app["bundle_version"],
        "bundle_identifier": app["bundle_id"],
        "ipa_name": asset["name"],
        "ipa_url": asset["browser_download_url"],
    }
    (output / "latest.json").write_text(
        json.dumps(latest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / ".nojekyll").touch()

    release_tag = html.escape(str(release["tag_name"]))
    short_version = html.escape(app["short_version"])
    build_number = html.escape(app["bundle_version"])
    bundle_id = html.escape(app["bundle_id"])
    ipa_url = html.escape(asset["browser_download_url"], quote=True)
    release_url = html.escape(release["html_url"], quote=True)
    install_href = html.escape(install_url, quote=True)

    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#111827">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <title>PiliPlus iOS 安装</title>
  <style>
    :root {{ color-scheme: light dark; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 24px;
      background: radial-gradient(circle at top, #2563eb 0, #111827 48%); color: #f9fafb; }}
    main {{ width: min(100%, 520px); padding: 32px; border: 1px solid rgba(255,255,255,.16);
      border-radius: 24px; background: rgba(17,24,39,.88); box-shadow: 0 24px 80px rgba(0,0,0,.35);
      backdrop-filter: blur(18px); }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    .subtitle {{ margin: 0 0 24px; color: #cbd5e1; }}
    dl {{ display: grid; grid-template-columns: auto 1fr; gap: 10px 16px; margin: 0 0 26px; }}
    dt {{ color: #94a3b8; }} dd {{ margin: 0; text-align: right; word-break: break-all; }}
    .install {{ display: block; padding: 15px 18px; border-radius: 14px; text-align: center;
      background: #3b82f6; color: white; text-decoration: none; font-weight: 700; font-size: 17px; }}
    .install:active {{ transform: scale(.99); background: #2563eb; }}
    .links {{ display: flex; justify-content: center; gap: 20px; margin-top: 18px; }}
    .links a {{ color: #93c5fd; }}
    .notice {{ margin-top: 26px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,.12);
      color: #cbd5e1; font-size: 14px; line-height: 1.65; }}
    ol {{ padding-left: 20px; margin-bottom: 0; }}
  </style>
</head>
<body>
  <main>
    <h1>PiliPlus iOS</h1>
    <p class="subtitle">个人签名 OTA 安装页</p>
    <dl>
      <dt>上游 Tag</dt><dd>{release_tag}</dd>
      <dt>应用版本</dt><dd>{short_version}（构建 {build_number}）</dd>
      <dt>Bundle ID</dt><dd>{bundle_id}</dd>
    </dl>
    <a class="install" href="{install_href}">在此 iPhone / iPad 上安装</a>
    <div class="links">
      <a href="{release_url}">查看 Release</a>
      <a href="{ipa_url}">下载 IPA</a>
    </div>
    <section class="notice">
      <strong>安装说明</strong>
      <ol>
        <li>请使用 iPhone 或 iPad 的 Safari 打开本页面并点击安装按钮。</li>
        <li>系统弹出确认框后选择“安装”，然后返回主屏幕等待完成。</li>
        <li>仅 provisioning profile 中已经登记 UDID 的设备可以安装。</li>
        <li>更新时直接再次点击安装；Bundle ID 和签名团队相同且构建号更高时会覆盖旧版本。</li>
      </ol>
    </section>
  </main>
</body>
</html>
"""
    (output / "index.html").write_text(page, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--site-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    release = fetch_json(f"https://api.github.com/repos/{args.repository}/releases/latest")
    ipa_assets = [
        asset for asset in release.get("assets", []) if asset["name"].lower().endswith(".ipa")
    ]
    if len(ipa_assets) != 1:
        raise RuntimeError(f"Expected one IPA asset in the latest Release, found {len(ipa_assets)}")

    with tempfile.TemporaryDirectory() as temporary_directory:
        ipa_path = Path(temporary_directory) / ipa_assets[0]["name"]
        download(ipa_assets[0]["browser_download_url"], ipa_path)
        app = read_app_metadata(ipa_path)

    write_site(args.output, args.site_url, release, ipa_assets[0], app)
    print(
        f"Generated OTA page for {release['tag_name']} "
        f"({app['short_version']} build {app['bundle_version']}, {app['bundle_id']})"
    )


if __name__ == "__main__":
    main()
