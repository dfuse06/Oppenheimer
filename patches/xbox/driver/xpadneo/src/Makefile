# SPDX-License-Identifier: GPL-2.0-only

ccflags-y += -DVERSION=\"DFUSE-1.0\"

obj-$(CONFIG_HID_XPADNEO_DFUSE) += hid-xpadneo.o

hid-xpadneo-y := \
	xpadneo/consumer.o \
	xpadneo/core.o \
	xpadneo/debug.o \
	xpadneo/device.o \
	xpadneo/events.o \
	xpadneo/keyboard.o \
	xpadneo/mappings.o \
	xpadneo/mouse.o \
	xpadneo/power.o \
	xpadneo/quirks.o \
	xpadneo/rumble.o \
	xpadneo/synthetic.o
