import sys
import time
import argparse
import logging
from pathlib import Path


def _get_parser():
    parser = argparse.ArgumentParser(
        prog="toggletest",
        description="Universal hardware toggle testing CLI",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan", help="List available serial ports")

    p_ping = sub.add_parser("ping", help="Check Arduino is responding")
    _add_port_args(p_ping)

    p_read = sub.add_parser("read", help="Read current pin state")
    _add_port_args(p_read)
    _add_pin_arg(p_read)
    p_read.add_argument("--raw", action="store_true")

    p_write = sub.add_parser("write", help="Drive a pin HIGH or LOW")
    _add_port_args(p_write)
    _add_pin_arg(p_write)
    p_write.add_argument("--state", choices=["high", "low", "1", "0"], required=True)

    p_tog = sub.add_parser("toggle", help="Flip current pin state")
    _add_port_args(p_tog)
    _add_pin_arg(p_tog)

    p_pulse = sub.add_parser("pulse", help="Drive HIGH then LOW")
    _add_port_args(p_pulse)
    _add_pin_arg(p_pulse)
    p_pulse.add_argument("--duration-ms", type=float, default=100.0)

    p_mon = sub.add_parser("monitor", help="Monitor toggle state changes")
    _add_port_args(p_mon)
    _add_pin_arg(p_mon)
    p_mon.add_argument("--duration", type=float, default=10.0)
    p_mon.add_argument("--hz", type=float, default=100.0)
    p_mon.add_argument("--debounce-ms", type=float, default=50.0)
    p_mon.add_argument("--output", help="Save events to CSV or JSON")
    p_mon.add_argument("--label", default=None)

    p_rep = sub.add_parser("report", help="Run monitor and print full report")
    _add_port_args(p_rep)
    _add_pin_arg(p_rep)
    p_rep.add_argument("--duration", type=float, default=10.0)
    p_rep.add_argument("--hz", type=float, default=100.0)
    p_rep.add_argument("--debounce-ms", type=float, default=50.0)
    p_rep.add_argument("--output-csv", help="Save events to CSV")
    p_rep.add_argument("--output-json", help="Save events to JSON")

    return parser


def _add_port_args(p):
    p.add_argument("--port", default=None)
    p.add_argument("--baud", type=int, default=9600)

def _add_pin_arg(p):
    p.add_argument("--pin", type=int, default=2)

def _make_backend(args):
    from .backends.arduino import ArduinoBackend
    return ArduinoBackend(port=getattr(args, "port", None),
                          baud_rate=getattr(args, "baud", 9600))


def cmd_scan(args):
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("No serial ports found.")
            return
        print(f"Found {len(ports)} serial port(s):\n")
        for p in ports:
            print(f"  {p.device:<20} {p.description}")
    except ImportError:
        print("pyserial not installed. Run: pip install pyserial")


def cmd_ping(args):
    backend = _make_backend(args)
    try:
        print(f"Connecting to {args.port or 'auto-detect'}...")
        backend.connect()
        print("✓ Arduino responded to PING — connection OK")
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)
    finally:
        backend.disconnect()


def cmd_read(args):
    from .toggle import Toggle
    backend = _make_backend(args)
    with backend:
        t = Toggle(backend, pin=args.pin, mode="INPUT")
        state = t.read_raw() if args.raw else t.read()
        print(f"Pin {args.pin}: {'HIGH (1)' if state else 'LOW  (0)'}")


def cmd_write(args):
    from .toggle import Toggle
    state = args.state in ("high", "1")
    backend = _make_backend(args)
    with backend:
        t = Toggle(backend, pin=args.pin, mode="OUTPUT")
        t.write(state)
        print(f"Pin {args.pin} → {'HIGH' if state else 'LOW'}")


def cmd_toggle(args):
    from .toggle import Toggle
    backend = _make_backend(args)
    with backend:
        t = Toggle(backend, pin=args.pin, mode="OUTPUT")
        new = t.toggle()
        print(f"Pin {args.pin} toggled → {'HIGH' if new else 'LOW'}")


def cmd_pulse(args):
    from .toggle import Toggle
    backend = _make_backend(args)
    with backend:
        t = Toggle(backend, pin=args.pin, mode="OUTPUT")
        print(f"Pin {args.pin} → pulse ({args.duration_ms}ms) ...", end=" ", flush=True)
        t.pulse(duration_ms=args.duration_ms)
        print("done")


def cmd_monitor(args):
    from .toggle import Toggle
    from .logger import ToggleLogger
    backend = _make_backend(args)
    label = args.label or f"pin{args.pin}"
    print(f"Monitoring pin {args.pin} for {args.duration}s at {args.hz}Hz...")
    tlog = ToggleLogger(session_name="cli_monitor")
    try:
        with backend:
            t = Toggle(backend, pin=args.pin, mode="INPUT",
                       debounce_ms=args.debounce_ms, label=label)
            t.on_change(lambda e: print(f"  [{e.timestamp:.4f}s] {e.state_label}"))
            tlog.attach(t)
            t.monitor(duration=args.duration, poll_hz=args.hz)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    print(f"\nTotal changes: {tlog.event_count}")
    if args.output:
        path = Path(args.output)
        tlog.to_json(path) if path.suffix == ".json" else tlog.to_csv(path)
        print(f"Saved to {args.output}")


def cmd_report(args):
    from .toggle import Toggle
    from .logger import ToggleLogger
    backend = _make_backend(args)
    tlog = ToggleLogger(session_name="cli_report")
    print(f"Running report: pin {args.pin} for {args.duration}s...\n")
    try:
        with backend:
            t = Toggle(backend, pin=args.pin, mode="INPUT",
                       debounce_ms=args.debounce_ms, label=f"pin{args.pin}")
            tlog.attach(t)
            t.monitor(duration=args.duration, poll_hz=args.hz)
    except KeyboardInterrupt:
        print("Stopped early.")
    tlog.print_report()
    if args.output_csv:
        print(f"CSV saved: {tlog.to_csv(args.output_csv)}")
    if args.output_json:
        print(f"JSON saved: {tlog.to_json(args.output_json)}")


COMMANDS = {
    "scan": cmd_scan, "ping": cmd_ping, "read": cmd_read,
    "write": cmd_write, "toggle": cmd_toggle, "pulse": cmd_pulse,
    "monitor": cmd_monitor, "report": cmd_report,
}


def main(argv=None):
    parser = _get_parser()
    args = parser.parse_args(argv)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    fn = COMMANDS.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()