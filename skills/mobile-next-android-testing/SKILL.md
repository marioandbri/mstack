---
name: mobile-next-android-testing
description: Tests and diagnoses Android apps on connected physical devices or emulators through Mobile Next mobile-mcp tools, with ADB fallback, accessibility-first interaction, screenshots, recordings, and crash evidence. Use when a user asks to test, reproduce, inspect, automate, or debug an Android or mobile app on a device, or mentions ADB, Mobile Next, mobile-mcp, APKs, Android emulators, or a connected phone.
---

# Mobile Next Android testing

Use Mobile Next to exercise the app as an end user would. Treat tool success as an action receipt, not proof that the app behaved correctly.

## Preflight

1. Call `mobile_list_available_devices` at the start of every session.
2. Select an online Android target and pass its returned ID as `device`. Never cache or hardcode a serial.
3. If no target appears, run `adb devices -l`:
   - `unauthorized`: ask the user to unlock the device and accept its debugging prompt.
   - `offline`: reconnect the device before testing.
   - no device: stop and report the missing target.
4. If the Mobile Next tools are absent, inspect `codex mcp list` or `/mcp`. A task opened before MCP configuration changed may require a new task or Codex restart.

## End-to-end workflow

1. Reproduce through the same user-visible entry point and sequence the user described.
2. Use the documented package name. If it is unknown, locate it with `mobile_list_apps`, then call `mobile_launch_app`.
3. Call `mobile_list_elements_on_screen` immediately before an interaction. Prefer its accessibility data and coordinates over screenshot guessing.
4. Tap, swipe, long-press, press a device button, or type only after resolving the current target. Confirm focus before `mobile_type_keys`.
5. Refresh `mobile_list_elements_on_screen` after every navigation or state change. Never reuse stale coordinates.
6. Assert the expected state after every meaningful action with a fresh element list or `mobile_take_screenshot`.
7. Capture the initial state, failure point, and final state. Use screen recording when a multi-step failure needs temporal evidence, and stop it before ending the task.
8. On a crash or unexpected exit, call `mobile_list_crashes`, then retrieve the relevant report with `mobile_get_crash`.
9. Report the exact path tested, observed result, expected result, target type, and evidence. Distinguish verified behavior from inference.

Install an APK with `mobile_install_app` only when installation is in scope and the exact APK path is known. Clean up by terminating only the app under test when needed.

## Physical-device safeguards

Treat any target reported as `real` as a personal physical device.

- Stay inside the requested app and test account.
- Do not clear data, uninstall apps, change system settings, send messages, make purchases, publish content, or access unrelated apps without explicit authorization.
- Do not expose credentials or personal data in screenshots, recordings, logs, or responses.
- Do not type real secrets. Ask the user for a safe test account or fixture when authentication is required.

## Evidence standard

The test passes only when the observed UI state proves the expected outcome. A response such as "tapped", "typed", or "launched" proves only that Mobile Next issued the command.
