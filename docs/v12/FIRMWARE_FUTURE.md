# Firmware, interrupts and RTOS future design (not implemented)

The generic integer-tick event contract can support a deterministic discrete-event model for interrupt scheduling, timer/PWM update, ADC/DMA, watchdog, task scheduling, preemption and deadline misses. Each event needs source, priority, execution cost, clock unit, and explicit tie-breaking semantics. Such a Python model must not be called firmware execution.

Renode is an optional later backend. A successful installation alone does not prove a specific STM32 peripheral or board is supported. Before registering firmware emulation, select a supported MCU/SoC and firmware image, verify peripheral models, and validate observable behavior. No firmware, RTOS, Renode, or hardware-in-the-loop adapter is READY in V12.
