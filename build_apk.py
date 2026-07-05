"""
Build script for AI Image Analyzer APK.

This script:
1. Runs `flet build apk` to generate the app shell and package Python
2. Excludes non-deliverable files such as .git, docs, tests, and sample images
3. Validates the generated APK so those files are not accidentally packaged
"""

import subprocess
import sys
import re
import hashlib
import io
import os
import zipfile
import tomllib
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
BUILD_FLUTTER_DIR = PROJECT_DIR / "build" / "flutter"
MANIFEST_PATH = BUILD_FLUTTER_DIR / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
APP_ZIP_PATH = BUILD_FLUTTER_DIR / "app" / "app.zip"
APP_ZIP_HASH_PATH = BUILD_FLUTTER_DIR / "app" / "app.zip.hash"
PYPROJECT_PATH = PROJECT_DIR / "pyproject.toml"
SITE_PACKAGES_DIR = PROJECT_DIR / "build" / "site-packages"
BUILD_STARTED_AT = 0.0
SERIOUS_PYTHON_ANDROID_VERSION = "1.0.1"

FLET_EXCLUDES = [
    ".git",
    ".pytest_cache",
    "build",
    "docs",
    "test_samples",
    "test_samples_personal",
    "tests",
    "__pycache__",
    ".gitignore",
    "*.pyc",
    "test_flet_log.txt",
    "test_flet_log2.txt",
]

FORBIDDEN_PACKAGE_PREFIXES = (
    ".git/",
    ".pytest_cache/",
    "build/",
    "docs/",
    "test_samples/",
    "test_samples_personal/",
    "tests/",
)

FORBIDDEN_PACKAGE_NAMES = {
    ".gitignore",
    "test_flet_log.txt",
    "test_flet_log2.txt",
}

def step1_flet_build():
    """Run flet build to generate template and package Python app."""
    global BUILD_STARTED_AT
    print("=" * 60)
    print("Step 1: Running flet build apk...")
    print("=" * 60)
    validate_android_dependencies()
    patch_serious_python_android_cache_download()
    BUILD_STARTED_AT = time.time()
    result = subprocess.run(
        [
            "flet",
            "build",
            "apk",
            "--module-name",
            "run",
            "--exclude",
            *FLET_EXCLUDES,
            "--yes",
            "--no-rich-output",
        ],
        cwd=str(PROJECT_DIR),
    )
    if result.returncode != 0:
        print("ERROR: flet build failed!")
        sys.exit(1)
    print("flet build completed successfully.\n")


def validate_android_dependencies():
    """Fail early for desktop-only packages that have no Android wheel."""
    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    deps = data.get("project", {}).get("dependencies", [])
    bad = [dep for dep in deps if dep.lower().startswith("pillow-heif")]
    if bad:
        print("ERROR: pillow-heif cannot be installed by the Android packager.")
        print("Move it to [project.optional-dependencies] or requirements.txt for desktop use.")
        sys.exit(1)


def patch_serious_python_android_cache_download():
    """Use cached Android Python archives without hitting GitHub on every build."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        print("WARNING: LOCALAPPDATA is not set; cannot patch serious_python_android cache handling.")
        return

    gradle_path = (
        Path(local_app_data)
        / "Pub"
        / "Cache"
        / "hosted"
        / "pub.dev"
        / f"serious_python_android-{SERIOUS_PYTHON_ANDROID_VERSION}"
        / "android"
        / "build.gradle"
    )
    if not gradle_path.exists():
        print(f"WARNING: serious_python_android Gradle file not found: {gradle_path}")
        return

    content = gradle_path.read_text(encoding="utf-8")
    patch_line = "        onlyIf { !dest.exists() }"
    if patch_line in content:
        print("serious_python_android cache patch already present.")
        return

    needle = '        doFirst { dest.parentFile.mkdirs() }\n'
    if needle not in content:
        print("WARNING: Could not find serious_python_android download hook to patch.")
        return

    gradle_path.write_text(content.replace(needle, needle + patch_line + "\n"), encoding="utf-8")
    print("Patched serious_python_android to use cached Python archives when present.")


def step2_patch_manifest():
    """Patch AndroidManifest.xml to allow cleartext HTTP traffic."""
    print("=" * 60)
    print("Step 2: Patching AndroidManifest.xml for cleartext traffic...")
    print("=" * 60)
    
    if not MANIFEST_PATH.exists():
        print(f"ERROR: Manifest not found at {MANIFEST_PATH}")
        sys.exit(1)
    
    content = MANIFEST_PATH.read_text(encoding="utf-8")
    
    if "usesCleartextTraffic" in content:
        print("Already patched, skipping.")
        return
    
    # Add usesCleartextTraffic="true" to the <application> tag
    patched = content.replace(
        'android:icon="@mipmap/ic_launcher">',
        'android:usesCleartextTraffic="true"\n        android:icon="@mipmap/ic_launcher">',
    )
    
    if patched == content:
        print("WARNING: Could not find insertion point in manifest!")
        print("Trying alternative pattern...")
        # Fallback: insert before the closing > of <application ...>
        patched = re.sub(
            r'(<application[^>]*)(>)',
            r'\1\n        android:usesCleartextTraffic="true"\2',
            content,
            count=1,
        )
    
    MANIFEST_PATH.write_text(patched, encoding="utf-8")
    print("Manifest patched successfully.\n")


def _is_forbidden_zip_entry(name: str) -> bool:
    normalized = name.replace("\\", "/").lstrip("/")
    if normalized in FORBIDDEN_PACKAGE_NAMES:
        return True
    return any(normalized.startswith(prefix) for prefix in FORBIDDEN_PACKAGE_PREFIXES)


def _write_app_zip_hash(path: Path) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    APP_ZIP_HASH_PATH.write_text(digest, encoding="utf-8")


def step3_sanitize_app_zip():
    """Remove repository/test artifacts from the Python app bundle before APK rebuild."""
    print("=" * 60)
    print("Step 3: Sanitizing packaged Python app.zip...")
    print("=" * 60)

    if not APP_ZIP_PATH.exists():
        print(f"ERROR: app.zip not found at {APP_ZIP_PATH}")
        sys.exit(1)

    tmp_path = APP_ZIP_PATH.with_suffix(".zip.tmp")
    removed_count = 0
    removed_bytes = 0

    with zipfile.ZipFile(APP_ZIP_PATH, "r") as src, zipfile.ZipFile(
        tmp_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as dst:
        for entry in src.infolist():
            if _is_forbidden_zip_entry(entry.filename):
                removed_count += 1
                removed_bytes += entry.file_size
                continue
            data = src.read(entry.filename)
            dst.writestr(entry, data)

    tmp_path.replace(APP_ZIP_PATH)
    _write_app_zip_hash(APP_ZIP_PATH)

    size_mb = APP_ZIP_PATH.stat().st_size / (1024 * 1024)
    removed_mb = removed_bytes / (1024 * 1024)
    print(
        f"Sanitized app.zip: removed {removed_count} entries "
        f"({removed_mb:.1f} MB uncompressed). New size: {size_mb:.1f} MB."
    )
    print("app.zip hash updated.\n")


def _validate_app_zip_bytes(data: bytes, source: str) -> None:
    with zipfile.ZipFile(io.BytesIO(data), "r") as app_zip:
        bad = [e.filename for e in app_zip.infolist() if _is_forbidden_zip_entry(e.filename)]
        if bad:
            preview = ", ".join(bad[:10])
            raise RuntimeError(f"{source} contains forbidden packaged files: {preview}")


def validate_app_zip(path: Path = APP_ZIP_PATH) -> None:
    _validate_app_zip_bytes(path.read_bytes(), str(path))


def validate_apk(apk_path: Path) -> None:
    with zipfile.ZipFile(apk_path, "r") as apk:
        app_entry = apk.getinfo("assets/flutter_assets/app/app.zip")
        data = apk.read(app_entry)
    _validate_app_zip_bytes(data, str(apk_path))

def step3_copy_apk():
    """Validate APKs generated by the Flet build."""
    print("=" * 60)
    print("Step 2: Validating generated APK package contents...")
    print("=" * 60)
    
    apk_dir = PROJECT_DIR / "build" / "apk"
    apk_files = list(apk_dir.glob("*.apk")) if apk_dir.exists() else []
    generated_apks = [
        apk for apk in apk_files
        if BUILD_STARTED_AT == 0.0 or apk.stat().st_mtime >= BUILD_STARTED_AT - 2
    ]
    
    if generated_apks:
        for apk in generated_apks:
            print(f"  Found generated APK: {apk}")
            try:
                validate_apk(apk)
                print("    package check: clean")
            except Exception as exc:
                print(f"    package check: FAILED - {exc}")
                sys.exit(1)
        older_apks = [apk for apk in apk_files if apk not in generated_apks]
        if older_apks:
            print("  Note: older APKs are still present and were not revalidated:")
            for apk in older_apks:
                print(f"    {apk}")
        print(f"\nAPK is ready in: {apk_dir}")
    elif apk_files:
        print("No newly generated APK could be identified; validating all APK files.")
        for apk in apk_files:
            print(f"  Found: {apk}")
            try:
                validate_apk(apk)
                print("    package check: clean")
            except Exception as exc:
                print(f"    package check: FAILED - {exc}")
                sys.exit(1)
        print(f"\nAPK is ready in: {apk_dir}")
    else:
        print("No APK found in build/apk. Check build output above.")

if __name__ == "__main__":
    step1_flet_build()
    validate_app_zip()
    step3_copy_apk()
    print("\n" + "=" * 60)
    print("BUILD COMPLETE!")
    print("=" * 60)
