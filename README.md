# Home Assistant Nova Poshta integration

Track your Nova Poshta parcels directly in Home Assistant — by TTN (tracking number).

> **Fork** of [krasnoukhov/homeassistant-nova-poshta](https://github.com/krasnoukhov/homeassistant-nova-poshta) with a completely reworked tracking approach.

## What's changed from the original

The original integration used `getDocumentList` API method which only returns parcels created via API/business cabinet. This fork uses `getStatusDocuments` — the same method the Nova Poshta app uses — which works for **any parcel received by phone number**.

| | Original | This fork |
|---|---|---|
| API method | `getDocumentList` | `getStatusDocuments` |
| Tracking | Auto-discovery by account | Manual TTN input |
| Sensors | One per warehouse | Four grouped sensors |
| Statuses | 7, 8 (at warehouse) | 4, 5, 6, 7, 8, 9, 10, 11, 12 |
| AliExpress / marketplace | ❌ | ✅ |

## Highlights

### Four sensors per account

- **В дорозі** (`mdi:truck-delivery`) — parcels in transit (statuses 4, 5, 6)
- **Чекає у відділенні** (`mdi:package-down`) — parcels waiting at branch or poshtomat (statuses 7, 8)
- **Отримано** (`mdi:package-check`) — received parcels (status 9)
- **Потребує уваги** (`mdi:alert-circle-outline`) — refused, returned, or problem parcels (statuses 10, 11, 12)

### Rich parcel attributes

Each sensor exposes full parcel details:

```yaml
parcels:
  - ttn: '20451424853965'
    status: Отримано
    description: Кава
    sender: КУЗЬМЕНКО МИХАЙЛО ІЛЛІЧ ФОП
    from: Тарасівка (Фастівський р-н)
    to: Львів
    warehouse: 'Відділення №96 (до 30 кг): вул. Пасічна, 166'
    weight_kg: '1.00'
    cost_uah: '90'
    announced_uah: 200
    scheduled: 28-04-2026 11:21:59
    received: 28.04.2026 19:52:37
    additional: ''
```

### Separate integration per person in the household

### Supports all parcel types

Works with any parcel delivered to your phone number: online shops, marketplaces (Rozetka, Prom, AliExpress), private senders, international shipments.

## Setup

You will need:
- Nova Poshta API key — get it at [new.novaposhta.ua](https://new.novaposhta.ua/dashboard/settings/developers)
- Your phone number in format `380XXXXXXXXX`
- TTN numbers of parcels you want to track (14 digits, comma-separated)

### Via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=igorolesko&repository=homeassistant-nova-poshta&category=Integration)

- Search for "Nova Poshta" in HACS
- Click three dots → Download
- Restart Home Assistant
- Go to Settings → Integrations → Add → Nova Poshta

### Manual Installation

- Copy the entire `custom_components/nova_poshta/` directory to `<config>/custom_components/`
- Restart Home Assistant
- Go to Settings → Integrations → Add → Nova Poshta

### Adding or removing TTNs

Go to Settings → Integrations → Nova Poshta → Configure. You can update the TTN list at any time without reinstalling.

## Example automation

Notification when a parcel arrives at the branch:

```yaml
alias: Nova Poshta — посилка у відділенні
trigger:
  - platform: state
    entity_id: sensor.nova_poshta_XXXXXXXXXX_nova_poshta_chekaie_u_viddilenni
    to:
    attribute: total
condition:
  - condition: numeric_state
    entity_id: sensor.nova_poshta_XXXXXXXXXX_nova_poshta_chekaie_u_viddilenni
    above: 0
action:
  - service: notify.mobile_app_your_phone
    data:
      title: 📦 Посилка у відділенні
      message: >
        {{ state_attr("sensor.nova_poshta_XXXXXXXXXX_nova_poshta_chekaie_u_viddilenni", "parcels")
           | map(attribute="description") | join(", ") }}
mode: single
```

Notification when a parcel is on its way:

```yaml
alias: Nova Poshta — посилка в дорозі
trigger:
  - platform: state
    entity_id: sensor.nova_poshta_XXXXXXXXXX_nova_poshta_v_dorozi
    attribute: total
action:
  - service: notify.mobile_app_your_phone
    data:
      title: 🚚 Посилка в дорозі
      message: >
        {{ state_attr("sensor.nova_poshta_XXXXXXXXXX_nova_poshta_v_dorozi", "parcels")
           | map(attribute="description") | join(", ") }}
mode: single
```

## Known limitations

- TTNs must be added manually — there is no automatic discovery
- Maximum 100 TTNs per account (API limit per request)
- Update interval: every 5 minutes
