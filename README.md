[![HACS][hacs-shield]][hacs-link]
[![GitHub Release][releases-shield]][releases-link]
[![Project Maintenance][maintenance-shield]][maintenance-link]

## Overview

This is a fork of [GeorgeSG/philips_airpurifier_http](https://github.com/GeorgeSG/philips_airpurifier_http), itself a hard fork of [xMrVizzy/philips-airpurifier](https://github.com/xMrVizzy/philips-airpurifier).

This is a custom Home Assistant component that enables you to control your Philips Air Purifier devices.
For now, it supports only older models that use the HTTP protocol for communication. CoAP support comming soon. :)

> **Tested on: Philips AC2889/10** (air purifier, no humidifier) — modes `auto`, `allergen`, `manual`, `bacteria`; speeds Silent, 1, 2, 3, Turbo.
> **Tested on: Philips AC3259/10** (air purifier, no humidifier) — modes `auto`, `allergen`, `manual`, `bacteria`, `sleep` [with patch applied]; speeds Silent, 1, 2, 3, Turbo.
> Other HTTP models (AC2729/10) are configured in `model_config.py` but haven't been tested with this fork.
> 

## Installation

### Install manually

Download the `philips_airpurifier_http` folder from this repo and place it in your `custom_components` folder

### Via HACS

Add this repo as a Custom Repository in HACS and install as an Integration from HACS' UI.

## Usage

Go to **Settings → Devices & services → Add integration → Philips AirPurifier (HTTP)** and enter the purifier's IP address and a name. Purifiers announcing themselves over SSDP also show up as discovered.

- **IP changed?** Use **Reconfigure** in the integration's ⋮ menu. It checks the new address answers and is the same purifier (by MAC). A rediscovered purifier at a new IP is updated automatically.
- **Purifier offline?** No restart needed: if it's unreachable at startup, Home Assistant keeps retrying setup in the background; once set up, the fan goes `unavailable` while it's offline and comes back by itself.

Give the purifier a DHCP reservation in your router so its IP doesn't drift.

### YAML (deprecated)

An existing YAML entry is imported into the UI automatically on startup; remove it from `configuration.yaml` afterwards.

```yaml
fan:
  platform: philips_airpurifier_http
  host: 192.168.0.17
  name: Philips Air Purifier # optional
```

---

## Entities

Besides the fan (power, mode, speed), each feature is its own entity on the purifier's device, ready to add to a dashboard. Only features the purifier reports are created — e.g. the AC2889/10 gets no humidifier entities.

| Entity                                                | Controls / shows                                                |
| ----------------------------------------------------- | --------------------------------------------------------------- |
| `light.<name>_light`                                  | Light on/off and brightness (snaps to 25/50/75/100; off is 0)   |
| `switch.<name>_child_lock`                            | Child lock                                                      |
| `switch.<name>_display_light`                         | Display light                                                   |
| `select.<name>_displayed_index`                       | Index shown on the purifier: `PM2.5` or `IAI`                   |
| `select.<name>_function`                              | Purification / Purification & Humidification (humidifiers only) |
| `select.<name>_target_humidity`                       | 40 / 50 / 60 % (humidifiers only)                               |
| `number.<name>_off_timer`                             | Off timer, 0–12 h                                               |
| `sensor.<name>_pm2_5`, `sensor.<name>_allergen_index` | Air quality readings                                            |
| `sensor.<name>_off_timer_remaining`                   | Minutes left on the off timer                                   |
| `sensor.<name>_{pre,hepa,carbon,wick}_filter`         | Filter life in hours (diagnostic)                               |
| `sensor.<name>_{temperature,humidity,water_level}`    | Humidifier models only                                          |

## Services

### `fan.set_preset_mode`

Set the device mode (if supported)

| Field       | Value               | Necessity  | Description                                              |
| ----------- | ------------------- | ---------- | -------------------------------------------------------- |
| entity_id   | `"fan.living_room"` | _Required_ | Name(s) of the entities to set mode                      |
| preset_mode | `"allergen"`        | _Required_ | One of "auto", "allergen", "sleep", "bacteria", "night". |

### `philips_airpurifier_http.set_function`

Set the device function (if supported)

| Field     | Value                             | Necessity  | Description                                               |
| --------- | --------------------------------- | ---------- | --------------------------------------------------------- |
| entity_id | `"fan.living_room"`               | _Required_ | Name(s) of the entities to set function                   |
| function  | `"Purification & Humidification"` | _Required_ | One of "Purification" or "Purification & Humidification". |

### `philips_airpurifier.set_target_humidity`

Set the device target humidity (if supported)

| Field     | Value               | Necessity  | Description                                    |
| --------- | ------------------- | ---------- | ---------------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set target humidity |
| humidity  | `40`                | _Required_ | One of 40, 50, 60                              |

### `philips_airpurifier.set_light_brightness`

Set the device light brightness

| Field     | Value               | Necessity  | Description                                                           |
| --------- | ------------------- | ---------- | --------------------------------------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set light brightness                       |
| level     | `50`                | _Required_ | One of 0, 25, 50, 75, 100. Turns off the display light if level is 0. |

### `philips_airpurifier_http.set_child_lock`

Set the device child lock on or off

| Field     | Value               | Necessity  | Description                               |
| --------- | ------------------- | ---------- | ----------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set child lock |
| lock      | `true`              | _Required_ | true or false                             |

### `philips_airpurifier_http.set_timer`

Set the device off time

| Field     | Value               | Necessity  | Description                              |
| --------- | ------------------- | ---------- | ---------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set off timer |
| hours     | `5`                 | _Required_ | Hours between 0 and 12                   |

### `philips_airpurifier_http.set_display_light`

Set the device display light on or off

| Field     | Value               | Necessity  | Description                                  |
| --------- | ------------------- | ---------- | -------------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set display light |
| light     | `true`              | _Required_ | true or false                                |

### `philips_airpurifier_http.set_used_index`

Sets the device used index(IAI or PM2.5)

| Field      | Value               | Necessity  | Description                                  |
| ---------- | ------------------- | ---------- | -------------------------------------------- |
| entity_id  | `"fan.living_room"` | _Required_ | Name(s) of the entities to set display light |
| used_index | `"IAI"`             | _Required_ | One of "IAI" or "PM2.5".                     |

## Meta

Original author: **Georgi Gardev**

- [gar.dev](https://gar.dev)
- [![GitHub][github-icon]][github-link] [GeorgeSG][github-link]
- [![Twitter][twitter-icon]][twitter-link] [@georgesg92][twitter-link]

[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-link]: https://github.com/hacs/integration
[releases-shield]: https://img.shields.io/github/v/release/Vortim/philips_airpurifier_http.svg
[releases-link]: https://github.com/Vortim/philips_airpurifier_http/releases
[maintenance-shield]: https://img.shields.io/maintenance/yes/2026.svg
[maintenance-link]: https://github.com/Vortim/philips_airpurifier_http
[github-icon]: http://i.imgur.com/9I6NRUm.png
[github-link]: https://github.com/GeorgeSG/
[twitter-icon]: http://i.imgur.com/wWzX9uB.png
[twitter-link]: https://twitter.com/georgesg92
