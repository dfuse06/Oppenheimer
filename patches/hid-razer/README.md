# DFUSE Razer HID

In-tree Linux kernel driver package for DFUSE Kernel Forge.

## What it does

- Copies the Razer HID driver into `drivers/hid/hid-razer`
- Wires the driver into `drivers/hid/Makefile`
- Wires the driver into `drivers/hid/Kconfig`
- Enables `CONFIG_HID_RAZER_DFUSE=m`
- Disables the stock `CONFIG_HID_RAZER`

## Notes

This driver package is based on OpenRazer driver sources and has been adjusted to build as one bundled kernel module.
