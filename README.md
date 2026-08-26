# PiliPlus iOS Build

This repository contains only the GitHub Actions workflow used to build and sign PiliPlus for iOS. The application source is checked out from [bggRGjQaUbCoE/PiliPlus](https://github.com/bggRGjQaUbCoE/PiliPlus) at build time and is not copied into this repository.

## Build behavior

- A manual run can build any upstream branch, tag, or commit.
- A scheduled run checks upstream `main` once per day. It builds only when the generated Release tag does not already exist.
- Every successful build uploads the signed IPA as a workflow artifact for 30 days.
- Scheduled runs publish a GitHub Release automatically. Manual runs publish a Release when `publish_release` is enabled.
- Generated Release tags use `ios-v<upstream-version>-<upstream-commit>` unless a manual run supplies a tag.

## Repository configuration

Configure these under **Settings → Secrets and variables → Actions**.

Repository secrets:

- `IOS_CERT_P12_BASE64`: Base64-encoded Apple signing certificate (`.p12`).
- `IOS_CERT_PASSWORD`: Password for the `.p12` file.
- `IOS_PROVISIONING_PROFILE_BASE64`: Base64-encoded provisioning profile (`.mobileprovision`).

Repository variables:

- `IOS_BUNDLE_ID`: Bundle ID covered by the provisioning profile. It may be left empty for an exact, non-wildcard profile.
- `IOS_EXPORT_METHOD`: `app-store-connect`, `release-testing`, `enterprise`, `debugging`, or `validation`. When empty, `release-testing` is used.

The workflow never prints certificate or provisioning-profile contents. Signing files are written only to the temporary GitHub-hosted runner and are removed after the build.

## Run manually

Open **Actions → Build signed iOS IPA → Run workflow**, choose the upstream ref, and decide whether to publish a Release. Leaving the Release tag empty gives the build a deterministic tag derived from the upstream version and commit.

PiliPlus is maintained in the upstream repository. Please report application issues there; this repository is only for the private signing/build configuration and generated iOS packages.
