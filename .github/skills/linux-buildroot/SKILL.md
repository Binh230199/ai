---
name: linux-buildroot
description: >
  Use when configuring, building, or customizing a Buildroot-based embedded
  Linux system. Covers menuconfig, BR2_EXTERNAL, package Config.in and .mk
  skeleton, toolchain options, output directory structure, and rootfs overlays
  for automotive IVI, HUD, and RSE targets.
argument-hint: <board-or-package> [configure|build|add-package]
---

# Buildroot — Embedded Linux Build System

Practices for building minimal embedded Linux root filesystems with
**Buildroot** for automotive IVI, HUD, and RSE targets.

Source of truth:
- [Buildroot Manual](https://buildroot.org/downloads/manual/manual.html)
- Buildroot source tree: `docs/manual/`

---

## When to Use This Skill

- Building a minimal, fast-booting root filesystem for a dedicated embedded device.
- Adding a custom package to a Buildroot build.
- Configuring a cross-compilation toolchain via Buildroot.
- Using `BR2_EXTERNAL` to keep project customizations outside the Buildroot tree.

---

## Buildroot vs. Yocto

| | Buildroot | Yocto |
|---|---|---|
| Complexity | Simple, fast to learn | Powerful but steep learning curve |
| Build system | Make + Kconfig | BitBake |
| Customization | Overlays, defconfigs, `BR2_EXTERNAL` | Layers, recipes, `.bbappend` |
| Package count | ~3000 | ~7000+ (with meta-oe) |
| Reproducibility | Good | Excellent (sstate cache) |
| Best for | Dedicated appliances, minimal images | Complex distros, SDK generation |

---

## Initial Configuration

```sh
# Configure for a supported board
make qemu_arm_versatile_defconfig   # example — use your target's defconfig

# Interactive configuration
make menuconfig

# Save current config as a named defconfig
make savedefconfig BR2_DEFCONFIG=configs/myboard_defconfig

# Load a saved defconfig
make myboard_defconfig
```

---

## menuconfig — Key Sections

| Menu section | What to configure |
|---|---|
| **Target options** | Architecture (ARM, AArch64, x86_64), CPU variant, endianness |
| **Toolchain** | Buildroot internal (crosstool-NG), external toolchain, musl/glibc/uClibc-ng |
| **System configuration** | Hostname, root password, init system (BusyBox / systemd), `/dev` management (udev / mdev) |
| **Kernel** | Linux kernel version, kernel configuration |
| **Target packages** | Application packages to include in the rootfs |
| **Filesystem images** | ext4, squashfs, wic, cpio, etc. |
| **Bootloaders** | U-Boot |

---

## Output Directory Structure

After `make`, output is in `output/`:

```
output/
  images/        # Final artifacts: kernel, dtb, rootfs image, u-boot.bin
  host/          # Cross-compilation toolchain + host build tools
  staging/       # Sysroot: headers and libraries for cross-compilation
  target/        # Root filesystem tree (not directly bootable)
  build/         # Per-package build directories
```

---

## Toolchain Options

### Buildroot internal toolchain (crosstool-NG)
Built from source. Configured under **Toolchain → Buildroot toolchain**. Slow on first build; cached afterwards.

### External toolchain
Use a pre-built toolchain (e.g., Linaro, ARM, your vendor's):
```
Toolchain type → External toolchain
Toolchain path → /opt/arm-linux-gnueabihf
```

Buildroot generates a wrapper and wires up `CC`, `CXX`, `LD` automatically.

---

## BR2_EXTERNAL — Keeping Customizations Outside Buildroot

`BR2_EXTERNAL` lets you maintain your project's configs, packages, and overlays in a separate tree:

```
my-bsp/                       # your external tree
  external.desc               # name and description (first line: name, second: desc)
  Config.in                   # root Config.in that includes package Config.in files
  external.mk                 # root .mk file that includes package .mk files
  configs/
    myboard_defconfig          # board defconfig
  package/
    my-app/
      Config.in
      my-app.mk
  board/
    myboard/
      rootfs-overlay/          # files copied on top of the rootfs
      post-build.sh            # script run after rootfs is assembled
      post-image.sh            # script run after image generation
```

`external.desc`:
```
name: MY_BSP
desc: My BSP customization layer
```

Using `BR2_EXTERNAL`:
```sh
make BR2_EXTERNAL=/path/to/my-bsp myboard_defconfig
make
```

---

## Adding a Custom Package

### Config.in

```kconfig
# package/my-app/Config.in
config BR2_PACKAGE_MY_APP
    bool "my-app"
    depends on BR2_TOOLCHAIN_HAS_THREADS
    help
      My automotive sensor application.
```

Include it from the external tree's `Config.in`:
```kconfig
source "$BR2_EXTERNAL_MY_BSP_PATH/package/my-app/Config.in"
```

### Package .mk file (Make-based)

```makefile
# package/my-app/my-app.mk
MY_APP_VERSION = 1.0
MY_APP_SITE = https://github.com/example/my-app
MY_APP_SITE_METHOD = git
MY_APP_GIT_SUBMODULES = YES

MY_APP_DEPENDENCIES = libdbus

define MY_APP_BUILD_CMDS
    $(MAKE) $(TARGET_CONFIGURE_OPTS) -C $(@D)
endef

define MY_APP_INSTALL_TARGET_CMDS
    $(INSTALL) -D -m 0755 $(@D)/my-app $(TARGET_DIR)/usr/bin/my-app
endef

$(eval $(generic-package))
```

Include from the external `.mk`:
```makefile
include $(sort $(wildcard $(BR2_EXTERNAL_MY_BSP_PATH)/package/*/*.mk))
```

### CMake-based package

```makefile
MY_APP_VERSION = 1.0
MY_APP_SITE = https://github.com/example/my-app
MY_APP_SITE_METHOD = git

MY_APP_CONF_OPTS = -DENABLE_CAN=ON

$(eval $(cmake-package))
```

---

## Rootfs Overlay

Files in `board/myboard/rootfs-overlay/` are copied verbatim on top of the target root filesystem after all packages are installed:

```
board/myboard/rootfs-overlay/
  etc/
    myapp.conf
    network/interfaces
  lib/
    systemd/system/
      my-app.service
```

Register the overlay in `BR2_ROOTFS_OVERLAY` (via menuconfig or defconfig):
```
BR2_ROOTFS_OVERLAY="board/myboard/rootfs-overlay"
```

---

## Post-Build and Post-Image Scripts

```sh
# board/myboard/post-build.sh — runs after packages installed, before image
#!/bin/sh
set -e
# Example: strip debug symbols
find "$TARGET_DIR/usr/bin" -type f -exec "$HOST_DIR/bin/arm-linux-strip" {} \;
```

```sh
# board/myboard/post-image.sh — runs after image generated
#!/bin/sh
set -e
# Example: create a combined firmware image
cat "$BINARIES_DIR/u-boot.bin" "$BINARIES_DIR/Image" > "$BINARIES_DIR/firmware.bin"
```

Register in defconfig / menuconfig:
```
BR2_ROOTFS_POST_BUILD_SCRIPT="board/myboard/post-build.sh"
BR2_ROOTFS_POST_IMAGE_SCRIPT="board/myboard/post-image.sh"
```

---

## Common Make Targets

```sh
make              # full build
make my-app       # build one package
make my-app-rebuild  # force rebuild a package
make my-app-dirclean # clean a package's build directory
make linux        # build only the kernel
make uboot        # build only U-Boot
make legal-info   # collect license information for all packages
make graph-depends  # generate dependency graph
```

---

## Prerequisites

- Linux host machine (Ubuntu 20.04 LTS or Debian 11 recommended).
- Cross-compilation toolchain: `arm-linux-gnueabihf-gcc` or `aarch64-linux-gnu-gcc`.
- Target board with serial console access (USB-to-UART adapter).
- `ssh` access to target (optional but recommended).


## Step-by-Step Workflows

### Step 1: Set up the Buildroot workspace
Clone or extract Buildroot; run `make <board>_defconfig` for your target board.

### Step 2: Configure with menuconfig
Run `make menuconfig` to enable/disable packages; save with `make savedefconfig`.

### Step 3: Create BR2_EXTERNAL (for custom packages)
Set up `Config.in`, `external.mk`, and `configs/` in your out-of-tree layer directory.

### Step 4: Add a custom package
Create `package/<name>/Config.in` and `package/<name>/<name>.mk`; include the package name in `external.mk`.

### Step 5: Build and verify
Run `make`; confirm the package is installed in `output/target/`; test on hardware.


## Troubleshooting

- **`make: *** No rule to make target`** — run `make clean` and retry; a stale stamp file may be causing the issue.
- **Package configuration not found** — verify the package `Config.in` is included in the parent `Config.in`; confirm `BR2_PACKAGE_<NAME>=y`.
- **Build fails with toolchain error** — rebuild the toolchain: `make toolchain-rebuild`; or switch to an external (pre-built) toolchain.
- **Target filesystem missing files** — check `package/<name>/<name>.mk` `do_install`; use `BR2_ROOTFS_OVERLAY` for additional static files.


## Pre-Commit Checklist

- [ ] `make savedefconfig` run; only non-default settings are in the defconfig.
- [ ] Package `Config.in` has a `help` section.
- [ ] Package `.mk` pins `VERSION` to a specific tag or commit hash — not `master`.
- [ ] `$(eval $(generic-package))` or `$(eval $(cmake-package))` at the end of `.mk`.
- [ ] Rootfs overlay files have correct permissions (`install -m` in post-build, or set directly).
- [ ] `BR2_EXTERNAL` path is relative or documented — not an absolute path to a developer machine.
- [ ] Full clean build (`make clean && make`) passes without errors.

---

## References

- [Buildroot Manual](https://buildroot.org/downloads/manual/manual.html)
- [Buildroot BR2_EXTERNAL](https://buildroot.org/downloads/manual/manual.html#outside-br-custom)
- [Buildroot package infrastructure](https://buildroot.org/downloads/manual/manual.html#_infrastructure_for_packages_with_specific_build_systems)
