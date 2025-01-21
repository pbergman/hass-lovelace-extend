# Lovelace Extend

This custom component for home assistant [lovelace dashboard](https://www.home-assistant.io/dashboards/) will make it possible to use the internal templating everywhere in the config. So you can create more dynamic dashboard with support for macro`s, inline templates (blocks) and vars in the hope to reduce duplication and create a more manageable dashboard config.

It works by reading the selected dashboard, parsing tree and storing the parsed tree simular as the normal dashboard works. For storage dashboards it will be registered as yaml, so we disable live editing (perhaps support in future) and add option to refresh which will reparse the source.     


## Installation

### Manually

- Clone/copy repository to `<your config dir>/custom_components/lovelace_extend/`.
- Restart Home Assistant

### Hacs

- Click the button below to open this repository in HACS:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pbergman&repository=hass-lovelace-extend&category=integration)
- Click add and then the download button in the bottom right corner.
- Restart Home Assistant

## Usage

Go to "Devices & services", and click "Add integration", search for `Lovelace Extend` and follow the instructions.

Or click the button below.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=lovelace_extend)

After that it will pop up a form with available dashboards, and you can select the desired dashboard which you like to be parsed/managed.

## Config

For every dashboard you can define dashboard scoped config under the `lovelace_extend` key in the root. Supported options for the dashboard rendering are:

### vars

Extra context vars which will added to the renderer

```yaml
lovelace_extend:
  vars:
    <name>: <str|list|dics>`
```

### exclude

To exclude properties of certain cards or whole cards you can define some paths or patterns to exclude card properties. The [basic format](custom_components/test/const.py#6) is card type between brackets followed by a property path or a pattern between less and greater sign. The path format is similar to json property paths and the card prefix can be a star to for all cards. 

The default is to ignore the `type` property for all cards:

```yaml
lovelace_extend:
  exclude:
    - "[*]type"
  
```

To exclude all properties for a card type you can define the type without a path  

```yaml
lovelace_extend:
  exclude:
    - "[custom:template]"
  
```

For (regex) patterns you have to define the pattern between `<` and `>`. So for example you have something like this

```yaml
lovelace_extend:
  exclude:
    - "[*]<(hold_action|tap_action)\.action>"
```

Which will excludes the `hold_action.action` and `tap_action.action` on all cards. 

### templates

Here you can define some inline template which you can [inherit](https://jinja.palletsprojects.com/en/stable/templates/#template-inheritance) later. So for example you have content block for users you could do something like   

```yaml
lovelace_extend:
  templates:
    foo: |
      {% block card %}
        Hello {% block name %}{% endblock %}
      {% endblock }
      
  vars:
    my_name: | 
      {% extends "foo" %}{% block name %}my_name{% endblock %}
```

### macros

All macro's will be autoloaded in the environment, so you don't need to include them and can be called directly by the name. Each macro can be defined with or without name arguments. 

With no named arguments

```yaml
lovelace_extend:
  macros:
    <name>: <content>
```

And with named argument

```yaml
lovelace_extend:
  macros:
    <name>:
      args:    <str|list>
      content: <str>
```
 
And simular to the template example you can do:

```yaml
lovelace_extend:
  macros: 
    foo: 
      args:
        - first_name
        - last_name=none
      content: My name is {{first_name}} {{last_name}}
  
  vars:
    my_name: "{{ foo('my_name') }}"
```

## Example

this example will register a variable which will call the defined macro and in the view we will use the variable. It`s bit of a strange example but should give you a picture what is possible.   

```yaml
lovelace_extend:
  vars:
    entities: "{{ get_device_entities_from_device('sensor.sun_next_dawn') }}"
    
  macros:
    get_device_entities_from_device:
        args: id
        content: "{{ device_entities(device_id(id)) }}"
          
views:
  - type: panel
    title: Dashboard
    cards:
      - type: entities
        entities: "{{ entities }}"
```

which will generate a dashboard like 

```yaml
views:
  - type: panel
    title: Dashboard
    cards:
      - type: entities
        entities:
            - sensor.sun_next_dawn
            - sensor.sun_next_dusk
            - sensor.sun_next_midnight
            - sensor.sun_next_noon
            - sensor.sun_next_rising
            - sensor.sun_next_setting

```
It is also possible to use a macro as a card template:

```yaml
lovelace_extend:
  macros:
    tile_card:
      args: entity
      content: |
        {% set card = {'type': 'tile', 'entity': entity } %}
        {% if kwargs|length > 0 %}
          {% set card = dict(card.items(), **kwargs) %}
        {% endif %}
        {{ card }}
          
views:
  - type: sections
    max_columns: 4
    title: Color test
    path: color-test
    sections:
      - type: grid
        cards:
          - type: heading
            heading: Color test
          - '{{ tile_card("sensor.sun_next_dawn") }}'
          - '{{ tile_card("sensor.sun_next_dawn", color="primary") }}'
          - '{{ tile_card("sensor.sun_next_dawn", color="accent") }}'
```

which will generate a dashboard like

```yaml
views:
  - type: sections
    max_columns: 4
    title: Color test
    path: color-test
    sections:
      - type: grid
        cards:
          - type: heading
            heading: Color test
          - type: tile
            heading:  "sensor.sun_next_dawn"
          - type: tile
            heading:  "sensor.sun_next_dawn"
            color: "primary"
          - type: tile
            heading:  "sensor.sun_next_dawn"
            color: "accent"
```