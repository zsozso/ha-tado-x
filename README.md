# Tado X for Home Assistant

A custom override of the Home Assistant Tado integration with Tado X cloud API
support. Based on the bundled **Home Assistant Core 2026.9.4** integration, with
`python-tado==0.19.2` and custom component version `2026.9.4.1`.

This is an independent community patch, not an official Tado integration.
It uses Tado's cloud service and requires internet access. It does not provide
local Matter control.

## What the patch changes

- Detects Tado X and maps room IDs and names to Home Assistant zones.
- Normalizes nested X device lists, serial numbers, device types and firmware.
- Supports X temperature, humidity, heating power and connectivity entities.
- Uses a 5.5–30 °C target range with 0.5 °C steps for X heating zones.
- Avoids self-referencing bridge relationships in device metadata.
- Skips heating-circuit API calls unsupported by X while retaining the select
  platform for older Tado devices.
- Preserves adaptive polling, HTTP user-agent identification and quota tracking
  with the pinned X-capable PyTado client.
- Removes refresh-token values from the modified debug messages.

Pre-X mapping is retained and covered by a compatibility test. This is a snapshot
for the stated Home Assistant version; compatibility with other releases is not
established.

## Installation

1. Back up your existing Tado integration and Home Assistant configuration.
2. Copy `custom_components/tado` from this repository into your Home Assistant
   configuration directory, producing `/config/custom_components/tado/manifest.json`.
   Merge only this component, not the entire configuration directory.
3. Run the Home Assistant configuration check:

   ```sh
   python -m homeassistant --script check_config --config /config
   ```

4. Restart Home Assistant. Its integration loader installs the dependency pinned
   in `manifest.json`.
5. Configure Tado through **Settings → Devices & services**, or use the existing
   Tado configuration entry. Complete reauthentication in the UI if requested.

This custom component uses the same `tado` domain as the bundled integration and
takes precedence over it. Do not configure a second copy of the same Tado home.
No credentials need to be placed in this repository or in YAML. Authentication
remains managed by Home Assistant.

HACS installation and automatic updates have not been validated; manual
installation is the supported procedure for this snapshot.

## Validation and limitations

Four isolated tests cover platform imports, quota tracking and user-agent
compatibility, X nested device mapping and climate readings/bounds, hot-water
zone type preservation, unsupported heating-circuit skipping and pre-X mapping.
They mock API access and use invented device identifiers. They do not operate
real thermostats or prove every device and service combination.

The component was also loaded successfully on Home Assistant 2026.9.4 with X
hardware. The full upstream Home Assistant test suite has not been run.
Cloud API changes, rate limits and authentication failures can still affect it.

To run the tests in a disposable container with Python 3.14 and matching Home
Assistant dependencies:

```sh
docker run --rm --entrypoint sh \
  -v "$PWD:/workspace:ro" -w /workspace \
  ghcr.io/home-assistant/home-assistant:2026.9.4 \
  -c 'pip install --target /tmp/tado-x-deps python-tado==0.19.2 && PYTHONPATH=/workspace:/tmp/tado-x-deps python -m unittest discover -s tests -v'
```

The dependency download requires internet access; the tests themselves make no
Tado cloud calls. No Home Assistant configuration volume is mounted.

## Upgrades and rollback

Before upgrading Home Assistant, compare this override with the bundled Tado
integration in the target release and rerun the compatibility tests. Updating
Home Assistant does not update files in `custom_components`.

To roll back, move the custom `tado` directory outside `custom_components` and
restart Home Assistant. The bundled integration and its declared dependency
will then be used. Custom X support may be lost. Do not restore old `.storage`
authentication files over the current configuration.

## Security and privacy

The repository contains integration source, translation resources and synthetic
tests only. Never commit Home Assistant `.storage`, configuration backups,
`secrets.yaml`, logs, diagnostics, OAuth tokens or personal device data.
If opening an issue, redact account, home, zone and device identifiers.

## License and origin

Derived from the Home Assistant Core Tado integration, released under the
Apache License 2.0; see [LICENSE](LICENSE). Original authorship is retained in
source metadata. The X compatibility changes are included under the same license.
For review, compare `custom_components/tado` with the
[upstream Tado integration at the 2026.9.4 tag](https://github.com/home-assistant/core/tree/2026.9.4/homeassistant/components/tado).
