### Mindbender Launcher

The Launcher provides an interface towards the file-system and environment.

![](https://cloud.githubusercontent.com/assets/2152766/25422623/6b46dab6-2a59-11e7-9642-9f27ca1c5383.gif)

<br>

**Table of contents**

| Section                           | Description
|:----------------------------------|:----------------
| [Inventory API](#inventory-api)   | Assets and shots, including metadata.
| [Definition API](#definition-api) | Tasks, applications and directory layout

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

assets:
  "Bruce":
  "Batman":
  "Camera":
  "Tarantula":

film:
  "1000":
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

##### Anatomy

The format of the inventory is as follows.

```yaml
{silo}
  "{asset}": {metadata}
```

| Key      | Description
|:---------|:----------
| silo     | Name of the current silo, such as `assets` or `film` (currently only these two are supported).
| asset    | Name of the given ASSET. All children of a silo is considered an ASSET, including shots.
| metadata | Optional metadata, as key: value entries.

<br>

##### Metadata

The metadata is made available as environment variables, prefixed with `MINDBENDER_`. For example, `edit_in` is made available for the given shot as `MINDBENDER_EDIT_IN`.

<br>

#### Definition API

The project definition contains the applications and tasks available within a given project, along with the template used to create directories.

**.config.yml**

```yaml
schema: mindbender-core:config-1.0

apps:
  - name: maya2016
  - name: nuke10
  - name: python
    args: [-u, -c, print('Something nice')]

tasks:
  - label: animation
    name: animation

  - label: modeling
    name: modeling

  - label: rigging
    name: rigging

  - label: lookdev
    name: lookdev

template:
    public: "{projectpath}/{silo}/{asset}/publish/{subset}/{version}/{subset}.{representation}"
    private: "{projectpath}/{silo}/{asset}/work/{task}/{user}/{app}"
```

##### Anatomy

The anatomy of a definition file contains three major sections.

| Section  | Description
|:---------|:-------------
| schema   | A pre-defined keyword to uniquely identify the format of this file.
| [apps](#apps)     | A list of dictionary elements, one per application
| [tasks](#tasks)    | A list of dictionary elements, one per task
| [template](#template) | A dictionary of template key/value pairs.

<br>

##### `apps`

Each app MAY contain the following members.

| Key     | Optional | Description
|:--------|:---------|:-------------
| name    | False    | Short name, used in the directory template.
| label   | True    | Nice name, used for presentation such as in the Launcher graphical user interface.
| args    | True     | A list of arguments passed to application at launch

##### `tasks`

Each task MAY contain the following members.

| Key     | Optional | Description
|:--------|:---------|:-------------
| name    | False    | Short name, used in the directory template.
| label   | True     | Nice name, used for presentation such as in the Launcher graphical user interface.

##### `templates`

The template defines the contained directory layout of each ASSET.
