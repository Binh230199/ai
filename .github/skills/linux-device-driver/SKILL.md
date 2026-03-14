---
name: linux-device-driver
description: >
  Use when writing, reviewing, or debugging Linux device drivers for embedded
  targets (automotive IVI, HUD, RSE on Linux/QNX-like kernels). Covers character
  device registration, struct file_operations, platform drivers with probe/remove,
  devm_* managed resources, memory-mapped I/O, and interrupt handling.
argument-hint: <driver-name> [write|review|debug]
---

# Linux Device Driver Development

Practices for writing correct, resource-safe Linux device drivers for embedded
targets such as **automotive IVI, HUD, and RSE** devices.

Source of truth:
- [Linux Device Drivers, 3rd Edition](https://lwn.net/Kernel/LDD3/)
- [Linux kernel — Documentation/driver-api/](https://www.kernel.org/doc/html/latest/driver-api/index.html)

---

## When to Use This Skill

- Writing a character device driver to expose hardware to userspace via `/dev/`.
- Writing a platform driver to control a device described in the Device Tree.
- Handling memory-mapped I/O registers.
- Installing interrupt handlers for hardware events.

---

## Character Device Driver

A character device exposes a file interface (`read`, `write`, `ioctl`) under `/dev/`.

```c
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>         // file_operations, alloc_chrdev_region
#include <linux/cdev.h>       // cdev_init, cdev_add, cdev_del
#include <linux/device.h>     // class_create, device_create
#include <linux/uaccess.h>    // copy_to_user, copy_from_user

#define DRIVER_NAME  "mydev"
#define DEVICE_NAME  "mydev0"

static dev_t         dev_num;
static struct cdev   my_cdev;
static struct class *my_class;

// --- file_operations callbacks ---

static int mydev_open(struct inode *inode, struct file *filp)
{
    pr_info(DRIVER_NAME ": open\n");
    return 0;
}

static int mydev_release(struct inode *inode, struct file *filp)
{
    pr_info(DRIVER_NAME ": release\n");
    return 0;
}

static ssize_t mydev_read(struct file *filp, char __user *buf,
                           size_t count, loff_t *ppos)
{
    const char *data = "hello\n";
    size_t len = strlen(data);

    if (*ppos >= len)
        return 0;  // EOF

    if (count > len - *ppos)
        count = len - *ppos;

    if (copy_to_user(buf, data + *ppos, count))
        return -EFAULT;

    *ppos += count;
    return count;
}

static ssize_t mydev_write(struct file *filp, const char __user *buf,
                            size_t count, loff_t *ppos)
{
    char kbuf[64] = {0};
    if (count >= sizeof(kbuf))
        count = sizeof(kbuf) - 1;

    if (copy_from_user(kbuf, buf, count))
        return -EFAULT;

    pr_info(DRIVER_NAME ": received: %s\n", kbuf);
    return count;
}

static const struct file_operations mydev_fops = {
    .owner   = THIS_MODULE,
    .open    = mydev_open,
    .release = mydev_release,
    .read    = mydev_read,
    .write   = mydev_write,
};

// --- init / exit ---

static int __init mydev_init(void)
{
    int ret;

    // Dynamically allocate a major number
    ret = alloc_chrdev_region(&dev_num, 0, 1, DRIVER_NAME);
    if (ret < 0) {
        pr_err(DRIVER_NAME ": alloc_chrdev_region failed: %d\n", ret);
        return ret;
    }

    // Initialize and add the cdev
    cdev_init(&my_cdev, &mydev_fops);
    my_cdev.owner = THIS_MODULE;
    ret = cdev_add(&my_cdev, dev_num, 1);
    if (ret < 0) {
        pr_err(DRIVER_NAME ": cdev_add failed: %d\n", ret);
        goto err_cdev;
    }

    // Create /sys/class/<DRIVER_NAME> and /dev/<DEVICE_NAME>
    my_class = class_create(THIS_MODULE, DRIVER_NAME);
    if (IS_ERR(my_class)) {
        ret = PTR_ERR(my_class);
        pr_err(DRIVER_NAME ": class_create failed: %d\n", ret);
        goto err_class;
    }

    if (IS_ERR(device_create(my_class, NULL, dev_num, NULL, DEVICE_NAME))) {
        ret = PTR_ERR(device_create(my_class, NULL, dev_num, NULL, DEVICE_NAME));
        pr_err(DRIVER_NAME ": device_create failed\n");
        goto err_device;
    }

    pr_info(DRIVER_NAME ": registered major=%d minor=%d\n",
            MAJOR(dev_num), MINOR(dev_num));
    return 0;

err_device:
    class_destroy(my_class);
err_class:
    cdev_del(&my_cdev);
err_cdev:
    unregister_chrdev_region(dev_num, 1);
    return ret;
}

static void __exit mydev_exit(void)
{
    device_destroy(my_class, dev_num);
    class_destroy(my_class);
    cdev_del(&my_cdev);
    unregister_chrdev_region(dev_num, 1);
    pr_info(DRIVER_NAME ": unregistered\n");
}

module_init(mydev_init);
module_exit(mydev_exit);
MODULE_LICENSE("GPL");
```

**Key rules:**
- `copy_to_user` / `copy_from_user` are mandatory for transferring data between kernel and userspace — never dereference a `__user` pointer directly.
- Always check the return value of kernel allocation/registration functions.
- Clean up in reverse order of setup on both the error path and in `__exit`.

---

## Platform Driver

A platform driver handles devices described in the Device Tree or board file.
It is matched by its `compatible` string.

```c
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>           // of_match_table, of_device_id
#include <linux/io.h>           // devm_ioremap_resource
#include <linux/interrupt.h>    // devm_request_irq
#include <linux/slab.h>         // devm_kzalloc

struct mydriver_priv {
    void __iomem *base;
    int irq;
};

static irqreturn_t mydriver_irq_handler(int irq, void *dev_id)
{
    struct mydriver_priv *priv = dev_id;
    // Read status register, clear interrupt, handle event
    (void)priv;
    return IRQ_HANDLED;  // IRQ_NONE if not our interrupt
}

static int mydriver_probe(struct platform_device *pdev)
{
    struct mydriver_priv *priv;
    struct resource *res;
    int ret;

    // Allocate private data — devm_ variant tied to device lifetime
    priv = devm_kzalloc(&pdev->dev, sizeof(*priv), GFP_KERNEL);
    if (!priv)
        return -ENOMEM;

    // Map hardware registers
    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    priv->base = devm_ioremap_resource(&pdev->dev, res);
    if (IS_ERR(priv->base))
        return PTR_ERR(priv->base);

    // Get and register interrupt
    priv->irq = platform_get_irq(pdev, 0);
    if (priv->irq < 0)
        return priv->irq;

    ret = devm_request_irq(&pdev->dev, priv->irq, mydriver_irq_handler,
                           0, dev_name(&pdev->dev), priv);
    if (ret)
        return ret;

    platform_set_drvdata(pdev, priv);
    dev_info(&pdev->dev, "probed successfully\n");
    return 0;
}

static int mydriver_remove(struct platform_device *pdev)
{
    // devm_* resources are freed automatically — add manual cleanup here if needed
    dev_info(&pdev->dev, "removed\n");
    return 0;
}

static const struct of_device_id mydriver_of_match[] = {
    { .compatible = "vendor,my-hardware" },
    { /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, mydriver_of_match);

static struct platform_driver mydriver = {
    .probe  = mydriver_probe,
    .remove = mydriver_remove,
    .driver = {
        .name           = "mydriver",
        .of_match_table = mydriver_of_match,
    },
};

module_platform_driver(mydriver);  // replaces module_init/module_exit boilerplate

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Example platform driver");
```

---

## `devm_*` — Managed Resources

Resources allocated with `devm_*` are automatically released when the device is
detached (`.remove` returns) or when the module is unloaded. This eliminates many
error-path and cleanup bugs.

| Manual API | Managed equivalent |
|---|---|
| `kzalloc` / `kfree` | `devm_kzalloc` (no free needed) |
| `ioremap_resource` / `iounmap` | `devm_ioremap_resource` |
| `request_irq` / `free_irq` | `devm_request_irq` |
| `request_mem_region` / `release_mem_region` | `devm_request_mem_region` |
| `clk_get` / `clk_put` | `devm_clk_get` |
| `gpio_request` / `gpio_free` | `devm_gpio_request` |

**Rule**: Prefer `devm_*` for all resource acquisition in `.probe`. Only mix manual
and managed resources when devm_ variants are not available for a specific API.

---

## Memory-Mapped I/O Register Access

```c
#include <linux/io.h>

// Read a 32-bit register
uint32_t val = readl(priv->base + REG_STATUS);

// Write a 32-bit register
writel(0x01, priv->base + REG_CONTROL);

// Read-modify-write
uint32_t ctrl = readl(priv->base + REG_CONTROL);
ctrl |= BIT(3);   // set bit 3
writel(ctrl, priv->base + REG_CONTROL);
```

**Rule**: Never access `void __iomem *` pointers directly with `*ptr` — always use
`readl`/`writel` (and their 8-/16-bit variants `readb`/`writeb`, `readw`/`writew`)
to ensure correct memory barriers on all architectures.

---

## Interrupt Handler Rules

- Keep the interrupt handler fast — do minimal work.
- Cannot sleep in an interrupt handler — do not call `kmalloc(GFP_KERNEL)` or `mutex_lock` from IRQ context.
- Use a work queue or tasklet to defer slow work.
- Return `IRQ_HANDLED` if the interrupt was from this device; `IRQ_NONE` otherwise.
- Shared interrupts (`IRQF_SHARED`) require `IRQ_NONE` when not yours.

---

## Device Tree Binding (Example)

```dts
/* board .dts */
my_sensor: sensor@40010000 {
    compatible = "vendor,my-hardware";
    reg = <0x40010000 0x1000>;  /* base address, size */
    interrupts = <0 32 IRQ_TYPE_LEVEL_HIGH>;
    clocks = <&clk_sensor>;
    status = "okay";
};
```

The driver matches on `compatible = "vendor,my-hardware"` and retrieves `reg`
and `interrupts` via `platform_get_resource` and `platform_get_irq`.

---

## ioctl — Custom Control Interface

```c
#include <linux/ioctl.h>

// Define ioctl command numbers — use _IO, _IOR, _IOW, _IOWR macros
#define MYDEV_IOC_MAGIC   'M'
#define MYDEV_GET_STATUS  _IOR(MYDEV_IOC_MAGIC, 1, uint32_t)
#define MYDEV_SET_MODE    _IOW(MYDEV_IOC_MAGIC, 2, uint32_t)

static long mydev_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
    uint32_t val;

    switch (cmd) {
    case MYDEV_GET_STATUS:
        val = read_hardware_status();
        if (copy_to_user((uint32_t __user *)arg, &val, sizeof(val)))
            return -EFAULT;
        return 0;

    case MYDEV_SET_MODE:
        if (copy_from_user(&val, (uint32_t __user *)arg, sizeof(val)))
            return -EFAULT;
        set_hardware_mode(val);
        return 0;

    default:
        return -ENOTTY;  // standard return for unknown ioctl
    }
}
```

---

## Prerequisites

- Linux host machine (Ubuntu 20.04 LTS or Debian 11 recommended).
- Cross-compilation toolchain: `arm-linux-gnueabihf-gcc` or `aarch64-linux-gnu-gcc`.
- Target board with serial console access (USB-to-UART adapter).
- `ssh` access to target (optional but recommended).


## Step-by-Step Workflows

### Step 1: Create the driver source file
Include `<linux/module.h>`, `<linux/kernel.h>`, and the subsystem-specific headers.

### Step 2: Register the device
Implement `probe()` and `remove()` for platform drivers; use `devm_*` functions for all resources.

### Step 3: Implement file operations (char device)
Fill `struct file_operations`; register with `misc_register()` or `cdev_add()`.

### Step 4: Handle memory-mapped I/O and interrupts
Use `devm_ioremap_resource()`; request IRQ with `devm_request_irq()`.

### Step 5: Build and test
Add to `Kconfig` and `Makefile`; load with `insmod`; verify with `dmesg` for registration messages.


## Troubleshooting

- **`insmod: ERROR: could not insert module`** — check `dmesg` immediately after; common causes: missing `MODULE_LICENSE`, symbol not found, or version mismatch.
- **`devm_request_irq` returns `-ENODEV`** — the IRQ number from DTS/platform data is wrong; verify with `/proc/interrupts`.
- **`ioremap` returns NULL** — the physical address is invalid or not reserved; check the memory map in the board DTS or BSP documentation.
- **Driver `probe()` not called** — confirm the `compatible` string in the driver matches the DTS node exactly (case-sensitive).


## Pre-Commit Checklist

- [ ] All `copy_to_user` / `copy_from_user` return values checked.
- [ ] Hardware registers accessed only via `readl`/`writel` (not pointer dereference).
- [ ] `devm_*` used for all resource allocation in `.probe`.
- [ ] `platform_get_irq` return value checked for negative.
- [ ] Interrupt handler does not sleep and returns `IRQ_HANDLED` or `IRQ_NONE`.
- [ ] Character driver: `alloc_chrdev_region` + `cdev_add` + `class_create` + `device_create`, with full cleanup on error path.
- [ ] Device Tree `compatible` string matches between driver and `.dts`.
- [ ] `MODULE_LICENSE`, `MODULE_AUTHOR`, `MODULE_DESCRIPTION` present.

---

## References

- [Linux Device Drivers, 3rd Edition (LDD3)](https://lwn.net/Kernel/LDD3/)
- [Linux Kernel Driver API](https://www.kernel.org/doc/html/latest/driver-api/index.html)
- [Device Tree Usage](https://www.kernel.org/doc/html/latest/devicetree/usage-model.html)
