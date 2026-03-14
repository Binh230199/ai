---
name: linux-kernel-development
description: >
  Use when configuring, building, patching, or reviewing Linux kernel code for
  embedded targets (automotive IVI, HUD, RSE on Linux). Covers Kconfig/menuconfig,
  defconfig, kernel source tree structure, Kbuild, cross-compilation, applying
  patches with git/quilt, and kernel versioning for BSP work.
argument-hint: <board-or-topic> [configure|build|patch|review]
---

# Linux Kernel Development

Practices for configuring, building, and patching the Linux kernel for embedded
**automotive IVI, HUD, and RSE** targets.

Source of truth:
- [Linux Kernel Documentation](https://www.kernel.org/doc/html/latest/)
- Kernel source tree: `Documentation/` and `Documentation/kbuild/`

---

## When to Use This Skill

- Configuring the kernel for a new board with `menuconfig` or `defconfig`.
- Adding or modifying `Kconfig` options and `Kbuild` targets.
- Cross-compiling the kernel for ARM/AArch64 from an x86 host.
- Applying or creating kernel patches with `git am` or `quilt`.
- Saving a reproducible board configuration with `savedefconfig`.
- Reviewing kernel code or driver integration for automotive BSP work.

---

## Kernel Source Tree Overview

```
linux/
  arch/          # architecture-specific code (arm, arm64, x86, ...)
  block/         # block layer
  drivers/       # device drivers (char, net, usb, video, ...)
  fs/            # filesystems
  include/       # public headers (linux/, asm/, uapi/)
  init/          # kernel init code (main.c, Kconfig)
  ipc/           # IPC subsystem
  kernel/        # core kernel (sched, lock, time, panic, ...)
  lib/           # kernel library functions
  mm/            # memory management
  net/           # networking stack
  scripts/       # build scripts and tools
  sound/         # ALSA audio subsystem
  tools/         # userspace tools (perf, bpftool, ...)
  Documentation/ # kernel documentation (RST)
```

---

## Kconfig — Kernel Configuration

The kernel uses **Kconfig** for feature selection. Configuration is stored in `.config`.

### Common config targets

```sh
# Interactive text-based menu
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- menuconfig

# Apply a saved defconfig (e.g., from arch/arm64/configs/)
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- <board>_defconfig

# Silently accept defaults for all unset symbols
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig

# Show differences between old and new config
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- listnewconfig
```

### Config fragments (merge_config.sh)

```sh
# Combine a base defconfig with one or more fragment files
scripts/kconfig/merge_config.sh arch/arm64/configs/myboard_defconfig \
    fragments/enable_cgroups.config \
    fragments/enable_bpf.config
```

This saves the merged result into `.config`.

---

## Building the Kernel

```sh
# Set these in shell or pass on every make invocation
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
export KDIR=/path/to/linux

# Build the kernel image (Image, zImage, uImage, etc.)
make -j$(nproc) Image

# Build device tree blobs
make -j$(nproc) dtbs

# Build all modules
make -j$(nproc) modules

# Install modules into a staging directory
make INSTALL_MOD_PATH=/path/to/staging modules_install
```

For ARM 32-bit:
```sh
export ARCH=arm
export CROSS_COMPILE=arm-linux-gnueabihf-
make <board>_defconfig
make -j$(nproc) zImage dtbs modules
```

### Out-of-tree build directory (O=)

```sh
mkdir -p /build/myboard
make O=/build/myboard ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- myboard_defconfig
make O=/build/myboard ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc) Image dtbs
```

---

## Kbuild — Kernel Build System

Every directory under the kernel tree contains a `Makefile` (called a **Kbuild Makefile**):

```makefile
# drivers/mydriver/Makefile
obj-$(CONFIG_MY_DRIVER) += mydriver.o
mydriver-objs := mydriver_core.o mydriver_hw.o
```

- `obj-y` → built into the kernel.
- `obj-m` → built as a module.
- `obj-$(CONFIG_SYMBOL)` → conditional on Kconfig symbol.

Corresponding `Kconfig` entry:

```kconfig
config MY_DRIVER
    tristate "My hardware driver"
    depends on I2C
    help
      Driver for my custom hardware.
      Say M to build as a module.
```

Add to parent `Kconfig` and `Makefile`:
```makefile
# drivers/Makefile
obj-y += mydriver/
```

```kconfig
# drivers/Kconfig
source "drivers/mydriver/Kconfig"
```

---

## Kernel Versioning

The kernel version is in the top-level `Makefile`:
```makefile
VERSION = 6
PATCHLEVEL = 1
SUBLEVEL = 0
EXTRAVERSION = -myboard
```

`uname -r` on the running system returns `<VERSION>.<PATCHLEVEL>.<SUBLEVEL><EXTRAVERSION>`.

Set `CONFIG_LOCALVERSION` in `.config` to add a local suffix: `CONFIG_LOCALVERSION="-ivi"`.

---

## Patching the Kernel

### Using git (recommended for BSP trees)

```sh
# Apply a patch series from a mailing list (git am)
git am 0001-fix-gpio-timeout.patch

# Apply a single patch file
git apply 0001-fix-gpio-timeout.patch

# Create a patch from a commit
git format-patch -1 HEAD            # last commit
git format-patch HEAD~3..HEAD       # last 3 commits
```

### Using quilt (for patch stacks on top of a release tarball)

```sh
quilt push          # apply next patch
quilt pop           # unapply last patch
quilt push -a       # apply all patches
quilt refresh       # update current patch with working-tree changes
quilt new 0001-my-fix.patch
quilt add drivers/mydriver/mydriver_core.c
# edit the file
quilt refresh
```

---

## Saving a Board defconfig

After configuring with `menuconfig`, save a minimal defconfig (only non-default values):

```sh
make ARCH=arm64 savedefconfig
cp defconfig arch/arm64/configs/myboard_defconfig
```

---

## Checking Kernel Config Symbols

```sh
# Find if a symbol is set
grep CONFIG_MY_FEATURE .config

# Show all values for a pattern
grep DMA .config | grep -v "^#"

# Verify the running kernel's config (if CONFIG_IKCONFIG_PROC=y)
zcat /proc/config.gz | grep CONFIG_MY_FEATURE
```

---

## Prerequisites

- Linux host machine (Ubuntu 20.04 LTS or Debian 11 recommended).
- Cross-compilation toolchain: `arm-linux-gnueabihf-gcc` or `aarch64-linux-gnu-gcc`.
- Target board with serial console access (USB-to-UART adapter).
- `ssh` access to target (optional but recommended).


## Step-by-Step Workflows

### Step 1: Set up the cross-compilation environment
Set `ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-` (adjust for your target architecture).

### Step 2: Configure the kernel
Start from the board defconfig: `make <board>_defconfig`; adjust with `make menuconfig`.

### Step 3: Apply patches
Use `git am` for patch series or `quilt push` for a quilt patch stack; review each patch.

### Step 4: Build the kernel
Run `make -j$(nproc)`; treat all new warnings as errors (`W=1` for stricter output).

### Step 5: Deploy and boot
Copy `Image` / `zImage` and DTB to the boot partition or TFTP server; boot and verify `uname -r`.


## Troubleshooting

- **`make` fails with `scripts/basic/fixdep: not found`** — run `make scripts_basic` first; or clean with `make mrproper` and reconfigure.
- **`Linux version mismatch` when loading module** — the module was built against a different kernel version; rebuild with `KERNEL_SRC` pointing to the running kernel tree.
- **Patch fails to apply** — check context with `patch --dry-run`; resolve conflicts manually and add a fixup commit.
- **Kernel panics on boot** — add `earlycon` and `initcall_debug` to kernel cmdline; capture serial output for the full log.


## Pre-Commit Checklist

- [ ] `savedefconfig` run and result committed along with functional changes.
- [ ] New `Kconfig` entries have a `help` text.
- [ ] New `obj-$(CONFIG_*)` entries added to the correct directory `Makefile`.
- [ ] Patch applies cleanly with `git am` or `git apply` — no fuzz or rejects.
- [ ] Build tested for both `=y` (built-in) and `=m` (module) if `tristate`.
- [ ] `ARCH` and `CROSS_COMPILE` confirmed for target, not host.
- [ ] `make dtbs` passes if device tree changes are included.

---

## References

- [Linux Kernel Documentation](https://www.kernel.org/doc/html/latest/)
- [Kbuild reference](https://www.kernel.org/doc/html/latest/kbuild/makefiles.html)
- [Kconfig language](https://www.kernel.org/doc/html/latest/kbuild/kconfig-language.html)
- [Submitting patches guide](https://www.kernel.org/doc/html/latest/process/submitting-patches.html)
