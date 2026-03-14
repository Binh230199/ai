---
name: linux-debugging
description: >
  Use when debugging embedded Linux systems targeting automotive IVI, HUD, and
  RSE devices. Covers serial console setup, kernel log analysis (dmesg/printk),
  remote debugging with gdbserver, JTAG via OpenOCD, ftrace, perf basics,
  /proc and /sys inspection, and reading kernel oops/panic messages.
argument-hint: <symptom-or-subsystem> [crash|hang|perf|driver]
---

# Embedded Linux Debugging

Practices for diagnosing and fixing issues on embedded **automotive IVI, HUD,
and RSE** Linux targets.

---

## When to Use This Skill

- Investigating a kernel crash (oops, panic, BUG).
- Tracing a suspected kernel-level performance regression.
- Debugging a device driver or kernel module remotely.
- Inspecting hardware state via `/proc` and `/sys`.

---

## Serial Console

The serial console (`ttyS0`, `ttyAMA0`, `ttyUSB0`, etc.) is the first diagnostic tool.

```sh
# Linux host — open serial port (115200 8N1)
picocom -b 115200 /dev/ttyUSB0
# or
minicom -b 115200 -D /dev/ttyUSB0
```

Kernel command line must include `console=<tty>,<baud>`:
```
console=ttyAMA0,115200
```

Add `ignore_loglevel` or set `loglevel=8` temporarily during bring-up to see all `printk` messages.

---

## Kernel Log — dmesg and printk

```sh
# Show kernel ring buffer
dmesg

# Show with timestamps (requires CONFIG_PRINTK_TIME=y or dmesg -T)
dmesg -T

# Follow new messages in real time
dmesg -w

# Filter by facility/level
dmesg --level=err,warn

# Clear the ring buffer
dmesg -C
```

### Dynamic debug — enable pr_debug() at runtime

```sh
# Enable debug messages for a specific file
echo "file drivers/mydriver/mydriver.c +p" > /sys/kernel/debug/dynamic_debug/control

# Enable for a whole module
echo "module mydriver +p" > /sys/kernel/debug/dynamic_debug/control

# Disable
echo "module mydriver -p" > /sys/kernel/debug/dynamic_debug/control
```

Requires `CONFIG_DYNAMIC_DEBUG=y`.

---

## Kernel Oops Analysis

A kernel oops appears on the serial console or in `dmesg`:

```
Unable to handle kernel NULL pointer dereference at virtual address 00000000
pgd = (ptrval)
[00000000] *pgd=00000000
Internal error: Oops: 5 [#1] PREEMPT SMP ARM
Modules linked in: mydriver
PC is at mydriver_read+0x28/0x6c [mydriver]
LR is at vfs_read+0x78/0x1c4
...
```

Key fields:
| Field | Meaning |
|---|---|
| `PC is at` | Instruction that caused the fault |
| `LR` | Link register — return address (where we came from) |
| `Oops: 5` | Fault status code (architecture-specific) |
| `#1` | This is the first oops since boot |
| `Call trace` | Stack frames at time of fault |

### Decoding with addr2line

```sh
# Decode a PC address to source line (using vmlinux with debug info)
aarch64-linux-gnu-addr2line -e vmlinux -f ffffffc0108abc28

# Decode a module address
aarch64-linux-gnu-addr2line -e mydriver.o -f 0x28
```

### scripts/decode_stacktrace.sh (kernel tree)

```sh
# Feed an oops through the decoder for fully resolved symbol names
dmesg | ./scripts/decode_stacktrace.sh vmlinux /path/to/modules
```

---

## Remote Debugging with gdbserver

```sh
# --- On the target ---
# Start gdbserver, attach to a running process
gdbserver :2345 /usr/bin/my-app          # new process
gdbserver --attach :2345 <pid>           # existing process

# --- On the host ---
aarch64-linux-gnu-gdb my-app
(gdb) target remote <target-ip>:2345
(gdb) break main
(gdb) continue
(gdb) bt                                 # backtrace
```

### Kernel debugging with KGDB

Requires `CONFIG_KGDB=y`, `CONFIG_KGDB_SERIAL_CONSOLE=y`, and the kernel command line:
```
kgdboc=ttyAMA0,115200 kgdbwait
```

On the host:
```sh
aarch64-linux-gnu-gdb vmlinux
(gdb) target remote /dev/ttyUSB1
```

---

## JTAG Debugging with OpenOCD

```sh
# Start OpenOCD with target and interface config files
openocd -f interface/ftdi/olimex-arm-usb-ocd-h.cfg -f target/stm32f4x.cfg

# In a separate terminal, connect GDB
arm-none-eabi-gdb vmlinux
(gdb) target remote localhost:3333
(gdb) monitor reset halt
(gdb) load                    # flash the image
(gdb) continue
```

OpenOCD listens on TCP port 3333 (GDB), 4444 (telnet CLI), 6666 (Tcl RPC) by default.

---

## ftrace — Kernel Function Tracer

ftrace is accessed via the `tracefs` filesystem, typically mounted at `/sys/kernel/debug/tracing/`.

```sh
# Mount debugfs if not already mounted
mount -t debugfs none /sys/kernel/debug

cd /sys/kernel/debug/tracing

# List available tracers
cat available_tracers

# Enable function tracer
echo function > current_tracer

# Trace specific functions matching a glob
echo "mydriver_*" > set_ftrace_filter

# Enable tracing
echo 1 > tracing_on

# Run your workload...

# Disable and read trace
echo 0 > tracing_on
cat trace

# Reset
echo > set_ftrace_filter
echo nop > current_tracer
```

### trace_printk (from kernel code)

```c
// Faster than printk for high-frequency tracing — output goes to ftrace ring buffer
trace_printk("mydriver: entered %s, value=%d\n", __func__, value);
```

Read with `cat /sys/kernel/debug/tracing/trace`.

---

## perf — Performance Analysis

```sh
# Record events for 10 seconds, all CPUs
perf record -a -g sleep 10

# Analyze recorded data
perf report

# Real-time top-like view
perf top -a

# Count specific hardware events for a command
perf stat -e cache-misses,cache-references ./my-app

# Trace kernel function calls
perf trace -e 'syscalls:sys_enter_read' ./my-app
```

Requires `CONFIG_PERF_EVENTS=y` in the kernel and `perf` binary built from kernel `tools/perf/`.

---

## /proc — Process and Kernel State

```sh
# CPU info
cat /proc/cpuinfo

# Memory usage
cat /proc/meminfo

# Interrupt counts per CPU
cat /proc/interrupts

# Loaded modules
cat /proc/modules

# Open file descriptors for a process
ls -la /proc/<pid>/fd

# Maps (virtual memory areas) of a process
cat /proc/<pid>/maps

# Kernel cmdline
cat /proc/cmdline

# Kernel messages (same as dmesg, read-only)
cat /proc/kmsg
```

---

## /sys — Sysfs Hardware State

```sh
# All network interfaces
ls /sys/class/net/

# Ethernet link state
cat /sys/class/net/eth0/operstate

# GPIO export and toggle (legacy sysfs GPIO interface)
echo 42 > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio42/direction
echo 1 > /sys/class/gpio/gpio42/value

# I2C adapters
ls /sys/class/i2c-adapter/

# Power management
cat /sys/power/state         # available sleep states
echo mem > /sys/power/state  # suspend to RAM
```

---

## Common Debugging Scenarios

### Driver not probing
```sh
# Check if the driver matched any device
dmesg | grep mydriver

# Check device tree nodes
find /sys/firmware/devicetree/base -name compatible | xargs grep -l my-hardware

# Check whether the driver is loaded
lsmod | grep mydriver

# Check platform devices
ls /sys/bus/platform/devices/
```

### Kernel module fails to load
```sh
insmod ./mydriver.ko
dmesg | tail -20   # look for error from init function
# Common causes: missing exported symbol, ABI mismatch, wrong kernel version
modinfo mydriver.ko  # check vermagic string
```

### Hung process
```sh
# Force a kernel dump of blocked tasks (requires CONFIG_DETECT_HUNG_TASK=y or manual trigger)
echo t > /proc/sysrq-trigger   # show blocked tasks in dmesg
echo l > /proc/sysrq-trigger   # show all CPUs' stack traces
```

---

## Prerequisites

- Linux host machine (Ubuntu 20.04 LTS or Debian 11 recommended).
- Cross-compilation toolchain: `arm-linux-gnueabihf-gcc` or `aarch64-linux-gnu-gcc`.
- Target board with serial console access (USB-to-UART adapter).
- `ssh` access to target (optional but recommended).


## Step-by-Step Workflows

### Step 1: Connect to the target
Use serial console (minicom/picocom at 115200 8N1) or SSH; confirm connection before starting.

### Step 2: Capture kernel logs
Run `dmesg | tail -50` and `journalctl -k` for recent kernel messages.

### Step 3: Identify the root cause
Match error messages against the common patterns documented in the sections below.

### Step 4: Set up remote debugging (if needed)
Start `gdbserver :1234 myapp` on target; attach with `arm-none-eabi-gdb` on host.

### Step 5: Verify the fix
Reboot or reload the module; confirm the issue does not recur; update team runbook.


## Troubleshooting

- **No serial output** — check baud rate (usually 115200 8N1) and cable; ensure `CONFIG_SERIAL_CONSOLE` is enabled in the kernel config.
- **`gdbserver` connection refused** — firewall or iptables may be blocking the port; try `iptables -F` on the target for debugging.
- **`dmesg` timestamp missing** — boot with `printk.time=1` kernel cmdline parameter.
- **ftrace ring buffer overflows** — increase buffer size: `echo 65536 > /sys/kernel/debug/tracing/buffer_size_kb`.


## Pre-Commit Checklist (for code that adds debugging hooks)

- [ ] `pr_debug` used for verbose traces — not `pr_info` (avoids log spam in production).
- [ ] `trace_printk` replaced with `pr_debug` before merging (trace_printk is for local debugging only).
- [ ] `WARN_ON`, `BUG_ON` used appropriately — `WARN_ON` for recoverable issues, `BUG_ON` only for truly unrecoverable states.
- [ ] No `printk(KERN_DEBUG ...)` left that floods the console at normal log levels.

---

## References

- [Kernel debugging guide](https://www.kernel.org/doc/html/latest/dev-tools/index.html)
- [ftrace documentation](https://www.kernel.org/doc/html/latest/trace/ftrace.html)
- [Dynamic debug](https://www.kernel.org/doc/html/latest/admin-guide/dynamic-debug-howto.html)
- [perf wiki](https://perf.wiki.kernel.org/index.php/Main_Page)
- [OpenOCD documentation](https://openocd.org/doc/html/index.html)
