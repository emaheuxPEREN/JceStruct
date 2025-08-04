import base64
import argparse
from pprint import pprint
from typing import Any, Callable, Optional

from jce import JceDecoder, types


def b64decode(s: str) -> bytes:
    altchars: Optional[str] = None
    if "+" not in s and "/" not in s and ("-" in s or "_" in s):
        altchars = "-_"  # URL-safe version
    if not s.endswith("="):  # add padding if needed
        s += "=" * (-len(s) % 4)
    return base64.b64decode(s, altchars=altchars, validate=True)


def b64encode(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


DECODERS = {
    "hex": bytes.fromhex,
    "b64": b64decode,
}

ENCODERS = {
    "hex": bytes.hex,
    "b64": b64encode,
    "raw": None,
}


def recursive_apply_on_bytes(obj: Any, fn: Callable[[bytes], Any]) -> Any:
    if isinstance(obj, bytes):
        return fn(obj)
    if isinstance(obj, list):
        return [recursive_apply_on_bytes(e, fn) for e in obj]
    if isinstance(obj, dict):
        return {k: recursive_apply_on_bytes(v, fn) for k, v in obj.items()}
    return obj


def cli() -> None:
    parser = argparse.ArgumentParser(description="JceStruct command line tool")
    parser.add_argument(
        "encoded",
        metavar="ENCODED",
        type=str,
        help="Encoded bytes in hex or base64 format",
    )
    parser.add_argument(
        "--keep-byte",
        action="store_true",
        help="Set this to keep byte (type 0 and 12) as raw bytes of length 1",
    )
    parser.add_argument(
        "--input-format",
        "-if",
        metavar="FORMAT",
        type=str,
        default="b64",
        help="Input encoding format ('b64', or 'hex')",
    )
    parser.add_argument(
        "--bytes-format",
        "-bf",
        metavar="FORMAT",
        type=str,
        default="raw",
        help="Output encoding format for bytes ('raw', 'b64', or 'hex')",
    )

    args = parser.parse_args()
    payload = DECODERS[args.input_format.lower()](args.encoded)
    result = JceDecoder.decode_bytes(
        payload,
        default_types=(
            None if args.keep_byte else {0: types.INT8, 12: types.ZERO_TAG_INT8}
        ),
    )

    bytes_encoder = ENCODERS[args.bytes_format.lower()]
    if bytes_encoder is not None:
        result = recursive_apply_on_bytes(result, bytes_encoder)

    pprint(result)


if __name__ == "__main__":
    cli()
