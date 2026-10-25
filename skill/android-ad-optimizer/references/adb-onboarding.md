# ADB Onboarding and Troubleshooting

Use this reference before inspection when the computer has not yet been authorized for the Android device.

## Phone-side checklist

1. Unlock the phone and connect a USB data cable.
2. Open `Settings > About phone`, then tap `Build number` repeatedly until Android confirms Developer options are enabled.
3. Open `Settings > System` or `Additional settings > Developer options`.
4. Enable `USB debugging` and confirm the warning.
5. When the RSA dialog appears, compare the computer fingerprint. Use `Always allow from this computer` only for a trusted computer.
6. Keep the screen unlocked while the agent performs notification UI operations.
7. Turn off `USB debugging` manually when the work is complete.

Menu names differ between ColorOS, HyperOS, MagicOS, OriginOS, One UI, and stock Android. If a menu is not found, search Settings for `Build number`, `Developer options`, or `USB debugging`; do not enable unrelated developer features.

## Computer-side checks

Run:

```text
adb devices
python scripts/android_ad_optimizer.py devices
```

Continue only when the intended device has state `device`.

| Result | Meaning | Safe next step |
|---|---|---|
| `adb` not found | Platform-Tools is missing or not on `PATH` | Install official Android SDK Platform-Tools or use its full executable path |
| no devices | Cable, USB mode, driver, or authorization issue | Unlock phone, try a data cable/USB port, choose a data mode, and check the RSA prompt |
| `unauthorized` | Phone has not approved this computer | Look at the unlocked phone and approve the fingerprint; do not bypass the prompt |
| `offline` | ADB transport is stale or unstable | Reconnect cable, unlock phone, close conflicting device tools, then retry |
| more than one `device` | Target is ambiguous | Ask the user which device to target; do not guess |
| `device` | Authorized and usable | Proceed to read-only inspection |

## Common recovery

- If the RSA prompt does not appear, keep the phone unlocked, reconnect the cable, switch USB ports, and check whether USB debugging is still enabled.
- If authorization is stale, the user can use `Developer options > Revoke USB debugging authorizations`, reconnect, and approve the new fingerprint. This is a phone-side action and requires confirmation from the user.
- On Windows, install an OEM USB driver only when Windows does not recognize the device; use the phone/OEM or Android developer documentation, not an arbitrary driver site.
- Do not enable wireless debugging, root access, bootloader unlocking, screen sharing, file transfer, or app installation unless the user separately asks and the workflow explicitly supports it.
- If the device disconnects during UI automation, stop, restore the connection, and re-run inspection before retrying. Do not repeat taps blindly.

Never proceed with settings changes while the state is `unauthorized`, `offline`, absent, or ambiguous.
