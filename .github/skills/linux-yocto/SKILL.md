---
name: linux-yocto
description: >
  Use when configuring, building, or debugging a Yocto Project-based Linux
  distribution for embedded targets. Covers BitBake, bblayers.conf, local.conf,
  recipe files (.bb / .bbappend), layers, image recipes, devtool, SDK generation,
  and common BSP layer patterns for automotive IVI, HUD, and RSE targets.
argument-hint: <recipe-or-layer> [write|build|debug]
---

# Yocto Project — Embedded Linux Distribution

Practices for building custom Linux images with the **Yocto Project** for
embedded automotive targets (IVI, HUD, RSE).

Source of truth:
- [Yocto Project Documentation](https://docs.yoctoproject.org/)
- [BitBake User Manual](https://docs.yoctoproject.org/bitbake/)

---

## When to Use This Skill

- Building a custom Linux root filesystem for an embedded board.
- Writing or modifying a BitBake recipe to add/change a package.
- Creating a BSP layer for a new hardware target.
- Generating an SDK for cross-compilation.

---

## Workspace Layout

```
poky/               # Yocto reference distribution (contains BitBake + OE-Core)
meta/               # OE-Core layer (included in poky)
meta-poky/          # Poky distro configuration
meta-openembedded/  # Extra packages (meta-oe, meta-networking, ...)
meta-<vendor>/      # Board vendor BSP layer
meta-<project>/     # Project-specific customizations
build/              # Build directory (created by oe-init-build-env)
  conf/
    bblayers.conf   # Which layers are included
    local.conf      # Build variables (MACHINE, DISTRO, parallelism, ...)
  tmp/              # Build output (sstate cache, sysroots, images)
    deploy/
      images/<MACHINE>/   # Final kernel, dtb, rootfs images
```

---

## Initial Setup

```sh
# Source the environment script — creates build/ if needed
source poky/oe-init-build-env build/

# After sourcing, you are in build/ and can run BitBake
```

---

## conf/bblayers.conf

```bitbake
BBLAYERS ?= " \
  /path/to/poky/meta \
  /path/to/poky/meta-poky \
  /path/to/meta-openembedded/meta-oe \
  /path/to/meta-myboard \
  /path/to/meta-project \
"
```

```sh
# Add a layer via command
bitbake-layers add-layer /path/to/meta-mylayer

# Show all layers and their priorities
bitbake-layers show-layers
```

---

## conf/local.conf — Key Variables

```bitbake
# Target machine (matches a .conf file in a layer's conf/machine/)
MACHINE = "myboard"

# Distribution policy
DISTRO = "poky"

# Parallelism
BB_NUMBER_THREADS = "8"
PARALLEL_MAKE = "-j 8"

# Package format
PACKAGE_CLASSES = "package_ipk"

# Extra packages to install in all images
IMAGE_INSTALL:append = " my-package another-package"

# Enable systemd
DISTRO_FEATURES:append = " systemd"
VIRTUAL-RUNTIME_init_manager = "systemd"
```

---

## Recipe Files (.bb)

```bitbake
# meta-project/recipes-example/my-app/my-app_1.0.bb

SUMMARY = "My automotive sensor application"
DESCRIPTION = "Reads CAN bus sensor data and publishes to D-Bus"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=abc123..."

SRC_URI = "git://github.com/example/my-app.git;branch=main;protocol=https"
SRCREV = "abc1234def5678..."

S = "${WORKDIR}/git"

inherit cmake

# CMake options
EXTRA_OECMAKE = "-DENABLE_CAN=ON"

# Files to install
do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${B}/my-app ${D}${bindir}/my-app
}
```

Key variables:
| Variable | Purpose |
|---|---|
| `S` | Source directory (extracted source) |
| `B` | Build directory |
| `D` | Destination directory (staging root for install) |
| `${bindir}` | `/usr/bin` |
| `${sbindir}` | `/usr/sbin` |
| `${libdir}` | `/usr/lib` |
| `${sysconfdir}` | `/etc` |
| `${systemd_unitdir}` | `/lib/systemd` |

---

## .bbappend — Modifying Existing Recipes

```bitbake
# meta-project/recipes-example/my-app/my-app_%.bbappend
# The % wildcard matches any version

# Append extra source files
SRC_URI:append = " file://0001-fix-timeout.patch"

# Append install steps
do_install:append() {
    install -d ${D}${sysconfdir}/my-app
    install -m 0644 ${WORKDIR}/my-app.conf ${D}${sysconfdir}/my-app/
}

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
```

---

## Image Recipes

```bitbake
# meta-project/recipes-core/images/my-ivi-image.bb

require recipes-core/images/core-image-minimal.bb

SUMMARY = "IVI minimal production image"

IMAGE_INSTALL:append = " \
    my-app \
    can-utils \
    dbus \
"

IMAGE_FEATURES:append = " ssh-server-openssh"
```

```sh
# Build the image
bitbake my-ivi-image
```

Images are placed in `build/tmp/deploy/images/<MACHINE>/`.

---

## Common BitBake Commands

```sh
# Build a recipe
bitbake my-app

# Build only a specific task
bitbake my-app -c compile
bitbake my-app -c devshell    # opens an interactive shell in the build environment

# Clean a recipe's work directory
bitbake my-app -c clean

# Clean and rebuild from scratch (removes sstate as well)
bitbake my-app -c cleansstate

# Show all tasks for a recipe
bitbake my-app -c listtasks

# Show which recipe provides a package
bitbake -s | grep my-app

# Show variable value as expanded by BitBake
bitbake -e my-app | grep ^WORKDIR

# Show all layers and recipes
bitbake-layers show-recipes
```

---

## devtool — Modifying Recipes Interactively

```sh
# Check out a recipe's source for editing
devtool modify my-app

# After editing, build and test
devtool build my-app
devtool build-image my-ivi-image

# Generate a patch from your changes and update the recipe
devtool update-recipe my-app

# Finish — moves changes back to the layer, cleans workspace
devtool finish my-app meta-project
```

---

## SDK Generation

```sh
# Build and populate the extensible SDK (eSDK)
bitbake my-ivi-image -c populate_sdk

# Installer is placed in:
# build/tmp/deploy/sdk/<distro>-<host>-<machine>-toolchain-<version>.sh
```

Install and use:
```sh
./poky-glibc-x86_64-my-ivi-image-aarch64-myboard-toolchain-*.sh
source /opt/poky/<version>/environment-setup-aarch64-poky-linux
# Now CROSS_COMPILE, CC, CXX, PKG_CONFIG_SYSROOT_DIR, etc. are set
```

---

## Creating a BSP Layer

```sh
# Use bitbake-layers to scaffold
bitbake-layers create-layer /path/to/meta-myboard
```

Minimal BSP layer structure:
```
meta-myboard/
  conf/
    layer.conf          # Layer config — BBPATH, BBFILES, layer deps
    machine/
      myboard.conf      # MACHINE definition
  recipes-kernel/
    linux/
      linux-myboard_%.bbappend  # Kernel .bbappend for the BSP
  recipes-bsp/
    u-boot/
      u-boot_%.bbappend
```

`conf/machine/myboard.conf`:
```bitbake
#@TYPE: Machine
#@NAME: My Board
require conf/machine/include/arm/arch-arm64.inc

KERNEL_IMAGETYPE = "Image"
UBOOT_MACHINE = "myboard_defconfig"
SERIAL_CONSOLES = "115200;ttyAMA0"

MACHINE_FEATURES = "usbgadget usbhost vfat"
IMAGE_FSTYPES = "ext4 wic"
```

---

## Prerequisites

- Linux host machine (Ubuntu 20.04 LTS or Debian 11 recommended).
- Cross-compilation toolchain: `arm-linux-gnueabihf-gcc` or `aarch64-linux-gnu-gcc`.
- Target board with serial console access (USB-to-UART adapter).
- `ssh` access to target (optional but recommended).


## Step-by-Step Workflows

### Step 1: Set up the build environment
Run `source oe-init-build-env`; configure `MACHINE` and `DISTRO` in `conf/local.conf`.

### Step 2: Add layers
Run `bitbake-layers add-layer <layer-path>`; verify with `bitbake-layers show-layers`.

### Step 3: Write or modify a recipe
Create `<name>_<version>.bb` or `.bbappend`; define `SRC_URI`, `do_install`, and `FILES`.

### Step 4: Build the image
Run `bitbake <image-name>`; use `bitbake -e <recipe>` to debug variable values.

### Step 5: Deploy to target
Flash the generated image (`wic`, `ext4`, or `tar.gz`) to the target storage medium.


## Troubleshooting

- **`ERROR: Nothing PROVIDES 'xxx'`** — the required layer is missing; add it with `bitbake-layers add-layer`; check `BBFILE_COLLECTIONS`.
- **Recipe fetch fails (404)** — the `SRC_URI` tarball URL has moved; update the URI and `SRC_URI[sha256sum]` checksum.
- **`do_compile` fails with cross-compiler error** — ensure `inherit cross-compilation` or `TOOLCHAIN` is correct; check `DEPENDS` for missing native tools.
- **Image boots but app is missing** — add the package name to `IMAGE_INSTALL:append` in `local.conf` or the image recipe.


## Pre-Commit Checklist

- [ ] `LIC_FILES_CHKSUM` present and correct in every new `.bb`.
- [ ] `SRCREV` pinned to a specific commit hash — not a branch name.
- [ ] `.bbappend` uses `FILESEXTRAPATHS:prepend` when adding local files.
- [ ] `do_install` creates all needed directories with `install -d`.
- [ ] `IMAGE_INSTALL:append` uses a leading space: `" package-name"`.
- [ ] New layer has a `conf/layer.conf` with correct `LAYERVERSION` and `LAYERDEPENDS`.
- [ ] `bitbake <recipe> -c cleansstate && bitbake <recipe>` passes from scratch.

---

## References

- [Yocto Project Documentation](https://docs.yoctoproject.org/)
- [BitBake User Manual](https://docs.yoctoproject.org/bitbake/)
- [OpenEmbedded Layer Index](https://layers.openembedded.org/)
- [devtool Quick Reference](https://docs.yoctoproject.org/ref-manual/devtool-reference.html)
