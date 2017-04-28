### Mindbender Launcher

The Launcher provides an interface towards the file-system and environment.

![untitled project](https://cloud.githubusercontent.com/assets/2152766/25536399/9e695010-2c32-11e7-8751-f249f62bd7e0.gif)

<br>

**Table of contents**

| Section                           | Description
|:----------------------------------|:----------------
| [Inventory API](#inventory-api)   | Assets and shots, including metadata.
| [Configuration API](#configuration-api) | Tasks, applications and directory layout
| [Executable API](#executable-api) | Applications, their directories and variables.

<br>

**Legend**

| Keyword   | Description
|:----------|:-------------
| ASSET     | Every project contains zero or more assets, shots are assets as well.

<br>

#### Inventory API

The inventory contains all ASSETs of a project, including metadata.

**.inventory.yml**

```yaml
schema: mindbender-core:inventory-1.0

# Available assets
assets:
  "Bruce":

    # An optional, nicer name.
    label: "Bruce Wayne"

    # An optional visual grouping.
    group: Character

  "Batman":
    group: Character
  "Camera":
    group: Prop
  "Tarantula":
    group: Prop

# Available shots
film:
  "1000":

    # Optional metadata per shot, available as environment
    # variables prefixed `MINDBENDER_`, e.g. `MINDBENDER_EDIT_IN`
    edit_in: 1000
    edit_out: 1143

  "1200":
    edit_in: 1000
    edit_out: 1081

  "2000":
  "2100":
  "2400":
```

The above is an example of an "inventory". A complete snapshot of all available assts within a given project, along with optional metadata.

<br>

#### Configuration API

The project configuration contains the applications and tasks available within a given project, along with the template used to create directories.

**.config.yml**

```yaml
schema: mindbender-core:config-1.0

# Project metadata, available as environment
# variables, prefixed `MINDBENDER_`
metadata:
    fps: 25
    resolution_width: 1920
    resolution_height: 1080

# Available applications to choose from, the name references
# the executable API (see below)
apps:
  - name: maya2016
  - name: nuke10
  - name: python
    args: [-u, -c, print('Something nice')]

# Available tasks to choose from.
tasks:
  - label: Character Animation
    name: animation

  - label: Modeling
    name: modeling

  - label: Character Rigging
    name: rigging

  - label: Look Development
    name: lookdev

# Directory layouts for this project.
template:
    work: "{projectpath}/{silo}/{asset}/work/{task}/{user}/{app}"
    publish: "{projectpath}/{silo}/{asset}/publish/{subset}/{version}/{subset}.{representation}"
```

<br>

### Executable API

Every executable must have an associated Application Definition file which looks like this.

```yaml
# Required header, do not touch.
schema: mindbender-core:application-1.0

# Name displayed in GUIs
label: "The Foundry Nuke 10.0"

# Name of the created directory, available in the 
# `template` of the Configuration API
application_dir: "nuke"

# Name of the executable on the local computer.
# This name must be available via the users `PATH`.
# That is, the user must be able to type this into
# the terminal to launch said application.
executable: "Nuke10.0"
```

The following options are available.

```yaml
schema: mindbender-core:application-1.0

label: "Autodesk Maya 2016x64"
description: ""
application_dir: "maya"
executable: "maya2016"

# These directories will be created under the
# given application directory
default_dirs:
    - scenes
    - data
    - renderData/shaders
    - images

# The environment variables overrides any previously set
# variables from the parent process.
environment:

    # Shorten time to boot
    MAYA_DISABLE_CIP: "Yes"
    MAYA_DISABLE_CER: "Yes"

    # Disable the AdSSO process
    MAYA_DISABLE_CLIC_IPM: "Yes"

    PYTHONPATH: [
        "{PYBLISH_MAYA}/pyblish_maya/pythonpath",
        "{MINDBENDER_CORE}/mindbender/maya/pythonpath",
        "{PYTHONPATH}",
    ]

# Arguments passed to the executable on launch
arguments: ["-proj", "{MINDBENDER_WORKDIR}"]

# Files copied into the application directory on launch
copy:
    "{MINDBENDER_CORE}/res/workspace.mel": "workspace.mel"
```