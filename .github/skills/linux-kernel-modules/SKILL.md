---
name: linux-kernel-modules
description: >
  Use when writing, building, or debugging Linux Loadable Kernel Modules (LKMs)
  for embedded Linux targets (automotive IVI, HUD, RSE). Covers module_init/exit
  macros, MODULE_LICENSE, Kbuild files, module parameters, printk logging, and
  insmod/rmmod/modprobe usage.
argument-hint: <module-name> [write|build|debug]
---

# Linux Kernel Modules (LKM)

Practices for writing correct, loadable kernel modules for embedded Linux targets
such as **automotive IVI, HUD, and RSE** devices.

Source of truth: [Linux Kernel Module Programming Guide](https://sysprog21.github.io/lkmpg/)
and the Linux kernel source tree (`Documentation/`).

---

## When to Use This Skill

- Writing a new out-of-tree kernel module for a device driver.
- Adding a lightweight kernel-space component that communicates via `/proc`, `/sys`, or `ioctl`.
- Building a module against a vendor kernel for Android/Linux embedded targets.

---

## Minimal Kernel Module

```c
// hello.c
#include <linux/module.h>   // module_init, module_exit, MODULE_*
#include <linux/kernel.h>   // printk, KERN_INFO

static int __init hello_init(void)
{
    printk(KERN_INFO "hello: module loaded\n");
    return 0;  // return 0 = success; non-zero = refuse to load
}

static void __exit hello_exit(void)
{
    printk(KERN_INFO "hello: module unloaded\n");
}

module_init(hello_init);
module_exit(hello_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Minimal example LKM");
```

**Rules:**
- `__init` marks the function reclaimable after the module loads (reduces kernel memory).
- `__exit` is discarded if the module is compiled into the kernel (not loadable).
- `MODULE_LICENSE("GPL")` is required for using GPL-exported kernel symbols. Without it, the kernel will mark itself as "tainted".
- `module_init` / `module_exit` register the init and cleanup entry points.

---

## Kbuild File

```makefile
# Kbuild — used by the kernel build system
obj-m += hello.o
```

For a module built from multiple source files:
```makefile
obj-m += mydriver.o
mydriver-objs := mydriver_core.o mydriver_hw.o mydriver_irq.o
```

---

## Out-of-Tree Build (Makefile)

```makefile
# Makefile — top-level build script invoked by the developer
KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
```

For cross-compilation (e.g., targeting ARM64 Android kernel):
```makefile
KDIR ?= /path/to/android/kernel/out/arch/arm64
ARCH := arm64
CROSS_COMPILE := aarch64-linux-gnu-

all:
	$(MAKE) -C $(KDIR) M=$(PWD) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) modules
```

---

## Module Parameters

```c
#include <linux/moduleparam.h>

static int debug_level = 0;
static char *device_name = "mydevice";
static int buffer_size = 4096;

module_param(debug_level, int, 0644);   // readable and writable via sysfs
module_param(device_name, charp, 0444); // read-only via sysfs
module_param(buffer_size, int, 0444);

MODULE_PARM_DESC(debug_level, "Debug verbosity level (0=off, 1=basic, 2=verbose)");
MODULE_PARM_DESC(device_name, "Name of the target device");
MODULE_PARM_DESC(buffer_size, "Internal buffer size in bytes");
```

Parameters can be set at load time:
```sh
insmod mymodule.ko debug_level=2 device_name=sensor0
```

Or at boot via `/etc/modprobe.d/mymodule.conf`:
```
options mymodule debug_level=1
```

The third argument to `module_param` is the sysfs permissions:
- `0` — not exposed in sysfs.
- `0444` — world-readable, not writable.
- `0644` — root-writable, world-readable.

---

## printk and Log Levels

```c
printk(KERN_EMERG   "system is unusable\n");          // 0
printk(KERN_ALERT   "action must be taken immediately\n"); // 1
printk(KERN_CRIT    "critical condition\n");           // 2
printk(KERN_ERR     "error condition\n");              // 3
printk(KERN_WARNING "warning condition\n");            // 4
printk(KERN_NOTICE  "normal but significant\n");       // 5
printk(KERN_INFO    "informational message\n");        // 6
printk(KERN_DEBUG   "debug-level message\n");          // 7
```

Use the `pr_*` shortcuts for shorter code:
```c
#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt  // adds "mymodule: " prefix

pr_info("driver initialized, version %s\n", DRIVER_VERSION);
pr_err("failed to allocate buffer: %d\n", ret);
pr_debug("entering %s\n", __func__);  // only active when dynamic debug or DEBUG defined
```

---

## Loading and Unloading

```sh
# Load a module (with dependencies resolved)
modprobe mymodule

# Load a specific .ko file (no dependency resolution)
insmod ./mymodule.ko

# Unload
rmmod mymodule

# Show loaded modules
lsmod | grep my

# Show module info (license, params, etc.)
modinfo mymodule.ko

# View kernel log
dmesg | tail -20
```

---

## Exporting Symbols

Other modules can call functions from your module if you export them:

```c
int my_public_function(int arg)
{
    return arg * 2;
}
EXPORT_SYMBOL(my_public_function);       // available to all modules
EXPORT_SYMBOL_GPL(my_public_function);   // available only to GPL-licensed modules
```

---

## Common Kernel APIs in Modules

| Need | API |
|---|---|
| Memory allocation | `kmalloc(size, GFP_KERNEL)` / `kfree(ptr)` |
| Zero-filled allocation | `kzalloc(size, GFP_KERNEL)` / `kfree(ptr)` |
| Mutex | `DEFINE_MUTEX(m)`, `mutex_lock(&m)`, `mutex_unlock(&m)` |
| Spinlock | `DEFINE_SPINLOCK(sl)`, `spin_lock_irqsave(&sl, flags)`, `spin_unlock_irqrestore(&sl, flags)` |
| Work queue | `INIT_WORK(&work, handler)`, `schedule_work(&work)` |
| Timer | `timer_setup(&t, callback, 0)`, `mod_timer(&t, jiffies + HZ)` |
| Wait queue | `DECLARE_WAIT_QUEUE_HEAD(wq)`, `wait_event_interruptible(wq, cond)`, `wake_up_interruptible(&wq)` |

**GFP flags for `kmalloc`:**
- `GFP_KERNEL` — may sleep; use in process context.
- `GFP_ATOMIC` — cannot sleep; use in interrupt context.

---

## Prerequisites

- Linux host machine (Ubuntu 20.04 LTS or Debian 11 recommended).
- Cross-compilation toolchain: `arm-linux-gnueabihf-gcc` or `aarch64-linux-gnu-gcc`.
- Target board with serial console access (USB-to-UART adapter).
- `ssh` access to target (optional but recommended).


## Step-by-Step Workflows

### Step 1: Create the module source file
Add `module_init()`, `module_exit()`, `MODULE_LICENSE("GPL")`, and module metadata macros.

### Step 2: Create the Kbuild file
Add `obj-m += mymodule.o` for out-of-tree builds or `obj-$(CONFIG_MY_MODULE) += mymodule.o` for in-tree.

### Step 3: Build the module
Run `make -C /lib/modules/$(uname -r)/build M=$(pwd) modules` for out-of-tree builds.

### Step 4: Load and test
Run `insmod mymodule.ko`; check `dmesg` for init messages; exercise the module functionality.

### Step 5: Unload and clean up
Run `rmmod mymodule`; confirm cleanup log messages appear; run `make clean`.


## Troubleshooting

- **`Unknown symbol in module`** — the symbol is defined but not exported; add `EXPORT_SYMBOL(symbol_name)` in the defining module.
- **`module verification failed: signature and/or required key missing`** — boot without `CONFIG_MODULE_SIG_FORCE` or sign the module with the kernel signing key.
- **Module loads but device not created** — `device_create()` or `misc_register()` may have failed silently; check the return value and `dmesg`.
- **Kernel oops on `insmod`** — enable `CONFIG_KASAN` in the kernel config; build the module with debug info and analyze the oops stack trace.


## Pre-Commit Checklist

- [ ] `MODULE_LICENSE` declared (usually `"GPL"` or `"Dual MIT/GPL"`).
- [ ] `module_init` and `module_exit` macros present.
- [ ] Init function returns 0 on success and a negative errno on failure.
- [ ] Cleanup function frees all resources allocated in init and in any other paths.
- [ ] No `GFP_KERNEL` allocation in interrupt context — use `GFP_ATOMIC`.
- [ ] Exported symbols use `EXPORT_SYMBOL_GPL` if they require GPL module consumers.
- [ ] Module parameters have `MODULE_PARM_DESC`.
- [ ] Cross-compilation `Makefile` sets `ARCH` and `CROSS_COMPILE`.

---

## References

- [Linux Kernel Module Programming Guide](https://sysprog21.github.io/lkmpg/)
- [Linux kernel — Documentation/kbuild/modules.rst](https://www.kernel.org/doc/html/latest/kbuild/modules.html)
- [Kernel printk and dynamic debug](https://www.kernel.org/doc/html/latest/admin-guide/dynamic-debug-howto.html)
