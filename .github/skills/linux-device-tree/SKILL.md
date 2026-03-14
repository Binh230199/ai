---
name: linux-device-tree
description: >
  Use when writing, reviewing, or debugging Linux Device Tree source files
  (DTS/DTSI) for embedded targets. Covers DTS node syntax, standard properties,
  phandles, common bindings (GPIO, pinctrl, clock, I2C, SPI, interrupt controller),
  DT overlays, dtc compiler, and binding verification for automotive BSP work.
argument-hint: <board-or-peripheral> [write|review|debug]
---

# Linux Device Tree (DTS / DTSI)

Practices for writing correct Device Tree source files for embedded
**automotive IVI, HUD, and RSE** targets.

Source of truth:
- [Linux Device Tree Usage](https://www.kernel.org/doc/html/latest/devicetree/usage-model.html)
- [Device Tree Specification](https://www.devicetree.org/specifications/)
- Binding documentation: `Documentation/devicetree/bindings/` in the kernel source

---

## When to Use This Skill

- Describing a new peripheral in the board DTS file.
- Enabling or disabling an existing node for your board.
- Writing a DT overlay for hardware add-ons.
- Verifying a binding against kernel documentation.

---

## DTS File Types

| Extension | Role |
|---|---|
| `.dts` | Top-level board file — included by the build system |
| `.dtsi` | Include file — shared between multiple boards (`/include/`) |
| `.dtbo` | Compiled overlay (binary form of a `.dts` overlay) |

---

## Basic Syntax

```dts
/dts-v1/;
#include "myvendor-soc.dtsi"   // include shared SoC DTSI

/ {
    model = "My Board Rev 1.0";
    compatible = "myvendor,myboard", "myvendor,mysoc";

    /* Memory node — required */
    memory@40000000 {
        device_type = "memory";
        reg = <0x0 0x40000000 0x0 0x80000000>;  // base 0x40000000, size 2 GiB (64-bit)
    };

    /* Chosen — kernel command line and stdout */
    chosen {
        bootargs = "console=ttyAMA0,115200 root=/dev/mmcblk0p2 rootwait";
        stdout-path = &uart0;
    };

    /* Aliases */
    aliases {
        serial0 = &uart0;
        mmc0 = &sdhci0;
    };
};
```

---

## Node Structure

```dts
node-name@unit-address {
    compatible = "vendor,model";     // string list — first is most specific
    reg = <base size>;               // physical address and size
    status = "okay";                 // "okay" or "disabled"
    // ... properties
};
```

**`#address-cells` and `#size-cells`** — tell how many 32-bit cells encode address and size in child `reg` properties:

```dts
soc {
    #address-cells = <1>;   // 1 cell for address (32-bit)
    #size-cells = <1>;      // 1 cell for size (32-bit)

    uart0: uart@40010000 {
        compatible = "arm,pl011";
        reg = <0x40010000 0x1000>;  // 1 address cell + 1 size cell
        // ...
    };
};
```

For 64-bit addresses:
```dts
#address-cells = <2>;
#size-cells = <2>;
uart0: uart@40010000 {
    reg = <0x0 0x40010000 0x0 0x1000>;
};
```

---

## Phandles and References

```dts
clocks: clock-controller@50000000 {
    compatible = "myvendor,clkctrl";
    reg = <0x50000000 0x1000>;
    #clock-cells = <1>;             // required for clock providers
};

&uart0 {
    clocks = <&clocks 3>;           // phandle to clocks node, clock ID = 3
    clock-names = "uartclk";
};
```

- `&uart0` is a reference to the node labeled `uart0:`.
- Referencing with `&label` merges properties into the target node.

---

## Common Bindings

### Interrupt Controller and Interrupts

```dts
intc: interrupt-controller@20000000 {
    compatible = "arm,cortex-a15-gic";
    reg = <0x20000000 0x1000 0x20010000 0x2000>;
    interrupt-controller;
    #interrupt-cells = <3>;
};

&uart0 {
    interrupt-parent = <&intc>;
    interrupts = <0 32 IRQ_TYPE_LEVEL_HIGH>;  // type, hwirq, flags
};
```

### GPIO

```dts
gpio0: gpio@40020000 {
    compatible = "myvendor,gpio";
    reg = <0x40020000 0x1000>;
    gpio-controller;
    #gpio-cells = <2>;             // pin number + flags
};

led {
    compatible = "gpio-leds";
    status-led {
        gpios = <&gpio0 3 GPIO_ACTIVE_HIGH>;
        default-state = "off";
    };
};
```

### Pinctrl

```dts
pinctrl0: pinctrl@40030000 {
    compatible = "myvendor,pinctrl";
    reg = <0x40030000 0x1000>;

    uart0_pins: uart0-pins {
        pins = "GPIO_A0", "GPIO_A1";
        function = "uart0";
        bias-pull-up;
    };
};

&uart0 {
    pinctrl-names = "default";
    pinctrl-0 = <&uart0_pins>;
};
```

### I2C Device

```dts
&i2c0 {
    clock-frequency = <400000>;   // 400 kHz Fast Mode

    temp_sensor: temperature@48 {
        compatible = "ti,lm75";
        reg = <0x48>;             // 7-bit I2C address
    };
};
```

### SPI Device

```dts
&spi0 {
    #address-cells = <1>;
    #size-cells = <0>;

    flash: flash@0 {
        compatible = "jedec,spi-nor";
        reg = <0>;                // chip select 0
        spi-max-frequency = <50000000>;
    };
};
```

---

## `status` Property

```dts
// Enable a disabled node from a DTSI
&uart1 {
    status = "okay";
};

// Disable a node that was enabled in the SoC DTSI
&usb0 {
    status = "disabled";
};
```

---

## DT Overlays

Overlays patch the live device tree at runtime (used for add-on boards, Raspberry Pi HATs, etc.):

```dts
/dts-v1/;
/plugin/;

&i2c0 {
    #address-cells = <1>;
    #size-cells = <0>;

    my_sensor: sensor@40 {
        compatible = "myvendor,my-sensor";
        reg = <0x40>;
        status = "okay";
    };
};
```

Apply at runtime:
```sh
dtoverlay my-sensor.dtbo
# or specify in /boot/config.txt (Raspberry Pi)
```

Specify in U-Boot FIT:
```
# Load base dtb, then apply overlay
fdt addr ${fdtaddr}
fdt resize 0x1000
fdt apply ${overlayaddr}
```

---

## dtc — Device Tree Compiler

```sh
# Compile DTS → DTB
dtc -I dts -O dtb -o myboard.dtb myboard.dts

# Decompile DTB → DTS (inspect a binary dtb)
dtc -I dtb -O dts -o myboard_decoded.dts myboard.dtb

# Check for errors only (no output file)
dtc -I dts -O dtb myboard.dts -o /dev/null
```

In the kernel build system, DTBs are compiled automatically:
```sh
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- dtbs
# Output: arch/arm64/boot/dts/<vendor>/myboard.dtb
```

---

## Verifying Bindings

Kernel binding documentation is in `Documentation/devicetree/bindings/` in RST or YAML format.

```sh
# Validate a DTS against YAML bindings (requires python3-jsonschema)
make ARCH=arm64 dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/serial/arm,pl011.yaml
make ARCH=arm64 dtbs_check
```

---

## Prerequisites

- Linux host machine (Ubuntu 20.04 LTS or Debian 11 recommended).
- Cross-compilation toolchain: `arm-linux-gnueabihf-gcc` or `aarch64-linux-gnu-gcc`.
- Target board with serial console access (USB-to-UART adapter).
- `ssh` access to target (optional but recommended).


## Step-by-Step Workflows

### Step 1: Identify the hardware node
Find the parent bus node in the board DTS/DTSI; prepare to add a child device node.

### Step 2: Set required properties
Add `compatible`, `reg`, `interrupts`, and subsystem-specific properties per binding docs.

### Step 3: Add phandle references
Add `clocks`, `resets`, `gpio`, and `pinctrl-*` references as needed by the driver.

### Step 4: Compile and check for errors
Run `dtc -I dts -O dtb -o output.dtb input.dts`; fix all compiler warnings.

### Step 5: Validate binding compliance
Run `dt-validate -p <schemas-path> output.dtb`; fix any schema constraint violations.


## Troubleshooting

- **`dtc` warning: `unit_address_vs_reg`** — node has a unit address but no `reg` property (or vice versa); either add `reg` or remove the unit address.
- **Driver not binding** — the `compatible` string in DTS must exactly match the driver's `of_match_table` entry (case-sensitive).
- **`dt-validate` schema not found** — pass the kernel `Documentation/devicetree/bindings/` path with `-p`; ensure the schema YAML is present.
- **DT overlay not applied** — check U-Boot `fdtoverlay apply` output; ensure `fdtfile` and overlay path are correct.


## Pre-Commit Checklist

- [ ] `compatible` string follows `"vendor,model"` format — no generic strings alone.
- [ ] `reg` cells match the parent node's `#address-cells` and `#size-cells`.
- [ ] `#gpio-cells`, `#clock-cells`, `#interrupt-cells` present on provider nodes.
- [ ] `status = "okay"` present on all nodes that must be active on this board.
- [ ] `dtc -I dts -O dtb` compiles without errors or warnings.
- [ ] `make dtbs_check` passes (if YAML bindings are available for the peripheral).
- [ ] Node labels (`uart0:`) are unique across all included DTSI files.

---

## References

- [Device Tree Usage (kernel.org)](https://www.kernel.org/doc/html/latest/devicetree/usage-model.html)
- [Device Tree Specification (devicetree.org)](https://www.devicetree.org/specifications/)
- [Kernel DT bindings documentation](https://www.kernel.org/doc/html/latest/devicetree/bindings/index.html)
- [DT overlays guide](https://www.kernel.org/doc/html/latest/devicetree/overlay-notes.html)
