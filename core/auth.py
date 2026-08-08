"""Admin check utilities.

Provides `is_admin()` which returns True when running as administrator. For tests
and CI, `AIPOLLON_FORCE_ADMIN=1` environment variable forces admin = True.
"""
import os
import platform
import sys

def is_admin() -> bool:
    # allow test override
    if os.environ.get("AIPOLLON_FORCE_ADMIN") == "1":
        return True

    if platform.system() != "Windows":
        # non-Windows: assume non-admin unless overridden
        return False

    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def main():
    ok = is_admin()
    print({"is_admin": ok})
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
