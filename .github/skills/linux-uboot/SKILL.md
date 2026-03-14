---
name: linux-uboot
description: >
  Use when implementing, configuring, or debugging U-Boot bootloader for embedded
  targets. Covers board porting (defconfig, board/ directory, include/configs/),
  U-Boot environment variables, boot scripts, FIT image creation with mkimage,
  SPL, driver model (DM), and flashing procedures for automotive BSP targets.
argument-hint: <board-or-topic> [port|configure|debug|flash]
---

# U-Boot Bootloader Development

Practices for configuring and porting **U-Boot** (Das U-Boot) for embedded
**automotive IVI, HUD, and RSE** targets.

Source of truth:
- [U-Boot Documentation](https://docs.u-boot.org/)
- U-Boot source tree: `doc/` and `README`

---

## When to Use This Skill

- Porting U-Boot to a new board (creating `board/` directory + defconfig).
- Configuring the boot sequence (`bootcmd`, `bootargs`).
- Creating FIT images to package kernel + dtb + initrd.
- Debugging early boot failures via serial console.

---

## U-Boot Source Tree Overview

```
u-boot/
  arch/          # architecture-specific code (arm, arm64, x86, ...)
  board/         # board-specific code (one directory per vendor/board)
  cmd/           # U-Boot shell commands
  common/        # Core U-Boot (environment, boot, autoboot, ...)
  drivers/       # Device drivers (mmc, usb, net, serial, ...)
  dts/           # Device tree sources used by U-Boot itself
  env/           # Environment handling
  fs/            # Filesystem support (fat, ext4, squashfs, ...)
  include/
    configs/     # Legacy board header files (Kconfig is replacing these)
  lib/           # Library code (crypto, compression, ...)
  tools/         # Host tools (mkimage, env tools, ...)
```

---

## Building U-Boot

```sh
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-

# Apply a board defconfig (stored in configs/<board>_defconfig)
make myboard_defconfig

# Optional: interactive configuration
make menuconfig

# Build
make -j$(nproc)

# Output:
#   u-boot       — ELF binary
#   u-boot.bin   — raw binary
#   u-boot.img   — image wrapped with mkimage header
#   spl/u-boot-spl.bin  — Secondary Program Loader (if SPL=y)
```

---

## Board Porting

### Directory structure for a new board

```
board/
  myvendor/
    myboard/
      Kconfig         # board-level Kconfig
      Makefile
      myboard.c       # board_init(), board_late_init(), dram_init(), etc.
      myboard.h       # (optional) board-specific header
      myboard.env     # (optional) environment defaults
```

### configs/myboard_defconfig

```kconfig
CONFIG_ARM=y
CONFIG_ARCH_MYVENDOR=y
CONFIG_TARGET_MYBOARD=y
CONFIG_DEFAULT_DEVICE_TREE="myboard"
CONFIG_SYS_TEXT_BASE=0x40080000
CONFIG_SPL=y
CONFIG_ENV_IS_IN_MMC=y
CONFIG_BOOTCOMMAND="run boot_mmc"
CONFIG_EXTRA_ENV_SETTINGS="boot_mmc=load mmc 0:1 ${loadaddr} Image; booti ${loadaddr} - ${fdtcontroladdr}\0"
```

### board/myvendor/myboard/Kconfig

```kconfig
if TARGET_MYBOARD

config SYS_BOARD
    default "myboard"

config SYS_VENDOR
    default "myvendor"

config SYS_CONFIG_NAME
    default "myboard"

endif
```

Register in `arch/arm/Kconfig` (for ARM boards):
```kconfig
source "board/myvendor/myboard/Kconfig"
```

---

## Environment Variables

U-Boot environment is a set of key=value pairs stored in flash/eMMC/SD.

```sh
# Show all environment variables
printenv

# Show one variable
printenv bootcmd

# Set a variable (session only — not persisted until saveenv)
setenv bootdelay 3

# Persist changes
saveenv

# Reset environment to compiled-in defaults
env default -a
saveenv
```

Common variables:
| Variable | Purpose |
|---|---|
| `bootcmd` | Command run after `bootdelay` seconds |
| `bootargs` | Kernel command line passed as `chosen/bootargs` |
| `loadaddr` | Address to load kernel/dtb into RAM |
| `fdtaddr` | Address for the device tree blob |
| `serverip` | TFTP server IP |
| `ipaddr` | Board IP address |
| `bootdelay` | Seconds before `bootcmd` runs (negative = disable autoboot) |

---

## Boot Scripts

```sh
# Load kernel and dtb from MMC partition 1, boot
setenv bootcmd "mmc dev 0; load mmc 0:1 ${loadaddr} /boot/Image; load mmc 0:1 ${fdtaddr} /boot/myboard.dtb; booti ${loadaddr} - ${fdtaddr}"

# Set kernel command line
setenv bootargs "console=ttyAMA0,115200 root=/dev/mmcblk0p2 rootwait rw"

# Test immediately without waiting for bootdelay
run bootcmd
```

Boot commands by image type:
| Image type | Boot command |
|---|---|
| ARM64 `Image` (uncompressed) | `booti <kernel_addr> - <fdt_addr>` |
| ARM32 `zImage` | `bootz <kernel_addr> - <fdt_addr>` |
| `uImage` (legacy) | `bootm <kernel_addr> - <fdt_addr>` |
| FIT image | `bootm <fit_addr>` |

---

## FIT Image — Flattened Image Tree

FIT images bundle kernel + dtb + (optionally) initrd into one signed/verified image.

### Image source file (.its)

```
/dts-v1/;
/ {
    description = "IVI kernel FIT image";
    #address-cells = <1>;

    images {
        kernel {
            description = "Linux kernel";
            data = /incbin/("Image");
            type = "kernel";
            arch = "arm64";
            os = "linux";
            compression = "none";
            load = <0x40080000>;
            entry = <0x40080000>;
            hash { algo = "sha256"; };
        };
        fdt {
            description = "Device tree";
            data = /incbin/("myboard.dtb");
            type = "flat_dt";
            arch = "arm64";
            compression = "none";
            hash { algo = "sha256"; };
        };
    };

    configurations {
        default = "conf";
        conf {
            kernel = "kernel";
            fdt = "fdt";
        };
    };
};
```

```sh
# Create the FIT image
mkimage -f myboard.its myboard.itb

# Boot it from U-Boot
load mmc 0:1 ${loadaddr} myboard.itb
bootm ${loadaddr}
```

---

## SPL — Secondary Program Loader

SPL is a minimal first-stage bootloader that fits in SRAM and loads the main U-Boot. Enable with `CONFIG_SPL=y`.

Key configs:
```kconfig
CONFIG_SPL=y
CONFIG_SPL_TEXT_BASE=0x00100000   # Load address in on-chip SRAM
CONFIG_SPL_MMC_SUPPORT=y
CONFIG_SPL_WATCHDOG=y
```

Boot flow: ROM → `spl/u-boot-spl.bin` → `u-boot.img` → kernel.

---

## Network Boot (TFTP)

```sh
# Set network parameters
setenv ipaddr 192.168.1.10
setenv serverip 192.168.1.1

# Download and boot kernel from TFTP
tftp ${loadaddr} Image
tftp ${fdtaddr} myboard.dtb
setenv bootargs "console=ttyAMA0,115200 root=/dev/nfs nfsroot=192.168.1.1:/nfs/rootfs,v3 ip=dhcp"
booti ${loadaddr} - ${fdtaddr}
```

---

## Flashing

Flash via U-Boot shell with `mmc write`:
```sh
# Write a raw image to MMC (offset in 512-byte blocks)
mmc dev 0
mmc write ${loadaddr} 0 0x2000   # write 0x2000 blocks (= 4 MiB) from loadaddr to sector 0
```

Flash via `fastboot` (if `CONFIG_USB_GADGET_DOWNLOAD=y`):
```sh
# On host
fastboot flash bootloader u-boot.img
fastboot flash boot Image
fastboot reboot
```

---

## Prerequisites

- Linux host machine (Ubuntu 20.04 LTS or Debian 11 recommended).
- Cross-compilation toolchain: `arm-linux-gnueabihf-gcc` or `aarch64-linux-gnu-gcc`.
- Target board with serial console access (USB-to-UART adapter).
- `ssh` access to target (optional but recommended).


## Step-by-Step Workflows

### Step 1: Set up the build environment
Set `ARCH`, `CROSS_COMPILE`; install `libssl-dev` and `swig` for signing/Python bindings.

### Step 2: Configure for the target board
Run `make <board>_defconfig`; adjust with `make menuconfig` or `make savedefconfig`.

### Step 3: Build U-Boot
Run `make -j$(nproc)`; locate `u-boot.bin`, `u-boot.img`, or `SPL` in the build output.

### Step 4: Flash to the target
Use `dd` to a raw partition, `fastboot flash bootloader`, or an OEM-provided flashing tool.

### Step 5: Set environment and verify boot
Connect serial console; configure `bootargs` and `bootcmd` env vars; confirm the kernel boots.


## Troubleshooting

- **U-Boot stops at `Hit any key to stop autoboot`** — set `bootdelay=0` in the environment for unattended boot; or pre-load the environment from flash.
- **`FIT image signature verification failed`** — the signing key in U-Boot does not match the key used to sign the FIT; re-sign or update the key in the device tree.
- **Environment variables lost after power cycle** — `saveenv` was not called; or the environment storage partition offset is wrong in the U-Boot config.
- **`tftpboot` times out** — verify network interface is `up` (`ping $serverip`); check TFTP server firewall rules and IP configuration.


## Pre-Commit Checklist

- [ ] Board `Kconfig` registered in the correct `arch/*/Kconfig`.
- [ ] `configs/<board>_defconfig` committed and `make <board>_defconfig && make` succeeds.
- [ ] `bootargs` set correctly — includes `console=`, `root=`, `rootwait`.
- [ ] `booti`/`bootz`/`bootm` used consistently with the kernel image type.
- [ ] FIT image `.its` file references correct file paths relative to mkimage invocation.
- [ ] SPL text base does not overlap with main U-Boot load address.
- [ ] Environment changes tested with `saveenv` + power cycle, not just `setenv`.

---

## References

- [U-Boot Documentation](https://docs.u-boot.org/)
- [U-Boot FIT images](https://docs.u-boot.org/en/latest/usage/fit/index.html)
- [U-Boot SPL framework](https://docs.u-boot.org/en/latest/develop/spl.html)
- [U-Boot environment](https://docs.u-boot.org/en/latest/usage/environment.html)
