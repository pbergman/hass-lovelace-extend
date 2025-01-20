# Lovelace Extend

This custom component for home assistant [lovelace dashboard](https://www.home-assistant.io/dashboards/) will make it possible to use templates everywhere to build a more dynamic dashboard with support for macro`s, inline templates (blocks) and vars.

This will work for yaml and storage dashboards but with storage templates you will not be able to edit them until you (temporary) disable the dashboard in the config.   

## Installation instructions

- clone/copy repository to `<your config dir>/custom_components/lovelace_extend/`.
- enable the lovelace extend in your integrations (settings > devices and services)
- choice dashboard extend (can also be done later with configuration)

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
