#!/usr/bin/env python3
"""Scan and compress oversized site images.

The script is dry-run by default. Pass --apply to rewrite images in place.
Compression uses Pillow when installed, otherwise macOS sips is used for JPEGs.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXTENSIONS = {".jpeg", ".jpg", ".png", ".webp"}
JPEG_EXTENSIONS = {".jpeg", ".jpg"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Find oversized images and optionally compress them."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["assets/photos"],
        help="Files or directories to scan. Defaults to assets/photos.",
    )
    parser.add_argument(
        "--threshold-mb",
        type=float,
        default=2.0,
        help="Only optimize files larger than this size. Default: 2.0.",
    )
    parser.add_argument(
        "--max-edge",
        type=int,
        default=2048,
        help="Resize images so the longest edge is at most this many pixels. Default: 2048.",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=82,
        help="JPEG/WebP output quality from 1 to 100. Default: 82.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Rewrite oversized images in place. Without this flag, only report.",
    )
    parser.add_argument(
        "--backup-dir",
        default=".image-backups",
        help="Directory for original-file backups when using --apply. Default: .image-backups.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create backups when using --apply.",
    )
    parser.add_argument(
        "--min-saving-kb",
        type=int,
        default=32,
        help="Keep an optimized file only if it saves at least this much. Default: 32.",
    )
    return parser.parse_args()


def human_size(size):
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return "{:.1f} {}".format(value, unit)
        value /= 1024
    return "{} B".format(size)


def iter_images(paths):
    seen = set()
    for item in paths:
        path = (ROOT / item).resolve() if not Path(item).is_absolute() else Path(item)
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            candidates = sorted(path.rglob("*"))
        else:
            print("Skipping missing path: {}".format(item), file=sys.stderr)
            continue

        for candidate in candidates:
            if not candidate.is_file():
                continue
            if candidate.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield candidate


def maybe_relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def has_pillow():
    try:
        import PIL  # noqa: F401
    except ImportError:
        return False
    return True


def has_sips():
    return shutil.which("sips") is not None


def backup_original(path, backup_dir):
    try:
        relative = path.resolve().relative_to(ROOT)
    except ValueError:
        relative = Path(path.name)
    destination = backup_dir / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copy2(str(path), str(destination))


def unlink_if_exists(path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def optimize_with_pillow(path, output, max_edge, quality):
    from PIL import Image, ImageOps

    with Image.open(str(path)) as image:
        image = ImageOps.exif_transpose(image)
        if max_edge:
            resample = getattr(Image, "Resampling", Image).LANCZOS
            image.thumbnail((max_edge, max_edge), resample)

        suffix = path.suffix.lower()
        if suffix in JPEG_EXTENSIONS:
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            image.save(
                str(output),
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
        elif suffix == ".png":
            image.save(str(output), format="PNG", optimize=True)
        elif suffix == ".webp":
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")
            image.save(str(output), format="WEBP", quality=quality, method=6)
        else:
            raise ValueError("Unsupported extension: {}".format(path.suffix))


def optimize_with_sips(path, output, max_edge, quality):
    if path.suffix.lower() not in JPEG_EXTENSIONS:
        raise ValueError("sips fallback only supports JPEG files")

    command = [
        "sips",
        "-s",
        "formatOptions",
        str(quality),
    ]
    if max_edge:
        command.extend(["-Z", str(max_edge)])
    command.extend([str(path), "--out", str(output)])

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def optimize_file(path, args, backend):
    original_size = path.stat().st_size
    suffix = path.suffix
    handle = tempfile.NamedTemporaryFile(
        prefix=".optimized-",
        suffix=suffix,
        dir=str(path.parent),
        delete=False,
    )
    output = Path(handle.name)
    handle.close()

    try:
        if backend == "pillow":
            optimize_with_pillow(path, output, args.max_edge, args.quality)
        elif backend == "sips":
            optimize_with_sips(path, output, args.max_edge, args.quality)
        else:
            raise ValueError("No image optimizer is available")

        optimized_size = output.stat().st_size
        min_saving = args.min_saving_kb * 1024
        if optimized_size >= original_size - min_saving:
            unlink_if_exists(output)
            return original_size, original_size, "kept"

        if not args.no_backup:
            backup_original(path, ROOT / args.backup_dir)
        shutil.copystat(str(path), str(output))
        output.replace(path)
        return original_size, optimized_size, "optimized"
    except Exception as exc:
        unlink_if_exists(output)
        return original_size, original_size, "error: {}".format(exc)


def main():
    args = parse_args()
    threshold = int(args.threshold_mb * 1024 * 1024)
    images = list(iter_images(args.paths))
    oversized = [path for path in images if path.stat().st_size > threshold]
    total_size = sum(path.stat().st_size for path in images)
    oversized_size = sum(path.stat().st_size for path in oversized)

    print("Scanned {} image files ({})".format(len(images), human_size(total_size)))
    print(
        "{} files are larger than {:.2f} MB ({})".format(
            len(oversized),
            args.threshold_mb,
            human_size(oversized_size),
        )
    )

    if not oversized:
        return 0

    backend = None
    if has_pillow():
        backend = "pillow"
    elif has_sips():
        backend = "sips"

    if not args.apply:
        print("\nDry run. Largest files:")
        for path in sorted(oversized, key=lambda item: item.stat().st_size, reverse=True)[:30]:
            print("  {:>9}  {}".format(human_size(path.stat().st_size), maybe_relative(path)))
        print("\nRun again with --apply to optimize.")
        if backend == "sips":
            print("Using sips fallback would optimize JPEG files only.")
        elif backend is None:
            print("Install Pillow to enable compression: python3 -m pip install Pillow")
        return 0

    if backend is None:
        print("No optimizer available. Install Pillow: python3 -m pip install Pillow", file=sys.stderr)
        return 1

    print("\nOptimizing with {}...".format(backend))
    before_total = 0
    after_total = 0
    optimized_count = 0
    kept_count = 0
    errors = []

    for path in sorted(oversized, key=lambda item: maybe_relative(item)):
        before, after, status = optimize_file(path, args, backend)
        before_total += before
        after_total += after
        if status == "optimized":
            optimized_count += 1
        elif status == "kept":
            kept_count += 1
        else:
            errors.append((path, status))
        print(
            "  {:<9} {:>9} -> {:>9}  {}".format(
                status.split(":", 1)[0],
                human_size(before),
                human_size(after),
                maybe_relative(path),
            )
        )

    print("\nOptimized {} files; kept {} already-small rewrites.".format(optimized_count, kept_count))
    print("Oversized-file total: {} -> {}".format(human_size(before_total), human_size(after_total)))
    print("Saved {}".format(human_size(before_total - after_total)))

    if errors:
        print("\nErrors:")
        for path, status in errors:
            print("  {}: {}".format(maybe_relative(path), status))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
