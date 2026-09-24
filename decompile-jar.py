#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import urllib.request

CFR_VERSION = "0.152"
CFR_URL = f"https://github.com/leibnitz27/cfr/releases/download/{CFR_VERSION}/cfr-{CFR_VERSION}.jar"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "decompile-jar")
CFR_JAR = os.path.join(CACHE_DIR, f"cfr-{CFR_VERSION}.jar")


def which(cmd):
    return shutil.which(cmd)


def find_java_in_common_locations():
    candidates = []

    if sys.platform == "win32":
        import glob
        candidates.extend(glob.glob(r"C:\Program Files\Eclipse Adoptium\*\bin\java.exe"))
        candidates.extend(glob.glob(r"C:\Program Files\Microsoft\jdk-*\bin\java.exe"))
        candidates.extend(glob.glob(r"C:\Program Files\Java\jdk-*\bin\java.exe"))
        candidates.extend(glob.glob(r"C:\Program Files\OpenJDK\*\bin\java.exe"))
    elif sys.platform == "darwin":
        candidates.append("/opt/homebrew/opt/openjdk/bin/java")
        candidates.append("/usr/local/opt/openjdk/bin/java")
        try:
            result = subprocess.run(
                ["/usr/libexec/java_home"], capture_output=True, text=True
            )
            if result.returncode == 0:
                candidates.append(os.path.join(result.stdout.strip(), "bin", "java"))
        except Exception:
            pass
    else:
        import glob
        candidates.extend(glob.glob("/usr/lib/jvm/*/bin/java"))

    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def ensure_java():
    if which("java") and which("javac"):
        return

    java_path = find_java_in_common_locations()
    if java_path:
        java_home = os.path.dirname(os.path.dirname(java_path))
        os.environ["JAVA_HOME"] = java_home
        os.environ["PATH"] = os.path.join(java_home, "bin") + os.pathsep + os.environ.get("PATH", "")
        print(f"Found Java at: {java_home}")
        return

    print("Java not found. Attempting to install...")

    if sys.platform.startswith("linux"):
        install_java_linux()
    elif sys.platform == "darwin":
        install_java_mac()
    elif sys.platform == "win32":
        install_java_windows()
    else:
        print(f"Error: unsupported platform '{sys.platform}'. Install Java manually.")
        sys.exit(1)

    java_path = find_java_in_common_locations()
    if java_path:
        java_home = os.path.dirname(os.path.dirname(java_path))
        os.environ["JAVA_HOME"] = java_home
        os.environ["PATH"] = os.path.join(java_home, "bin") + os.pathsep + os.environ.get("PATH", "")
        print(f"Using Java at: {java_home}")
        return

    print("Error: Java installation failed or not found.")
    print("Please install a JDK manually from https://adoptium.net/")
    sys.exit(1)


def install_java_linux():
    managers = [
        (["apt-get", "install", "-y", "default-jdk"], ["sudo", "apt-get", "update"]),
        (["dnf", "install", "-y", "java-17-openjdk-devel"], None),
        (["yum", "install", "-y", "java-17-openjdk-devel"], None),
        (["pacman", "-S", "--noconfirm", "jdk-openjdk"], None),
        (["apk", "add", "openjdk17-jdk"], None),
        (["zypper", "install", "-y", "java-17-openjdk-devel"], None),
    ]

    for install_cmd, update_cmd in managers:
        if which(install_cmd[0]):
            try:
                if update_cmd:
                    print(f"Running: {' '.join(update_cmd)}")
                    subprocess.run(update_cmd, check=False)
                cmd = install_cmd
                if os.geteuid() != 0:
                    cmd = ["sudo"] + cmd
                print(f"Running: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
                return
            except subprocess.CalledProcessError:
                continue

    print("Error: could not auto-install Java. Install it manually from https://adoptium.net/")


def install_java_mac():
    if which("brew"):
        try:
            print("Installing OpenJDK via Homebrew...")
            subprocess.run(["brew", "install", "openjdk"], check=True)
            try:
                result = subprocess.run(
                    ["/usr/libexec/java_home"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    java_home = result.stdout.strip()
                    os.environ["JAVA_HOME"] = java_home
                    os.environ["PATH"] = os.path.join(java_home, "bin") + os.pathsep + os.environ.get("PATH", "")
                    return
            except Exception:
                pass
            return
        except subprocess.CalledProcessError:
            pass

    print("Error: Homebrew not found. Install Java manually from https://adoptium.net/")


def install_java_windows():
    if which("winget"):
        try:
            print("Installing OpenJDK via winget...")
            subprocess.run(
                ["winget", "install", "-e", "--id", "EclipseAdoptium.Temurin.17.JDK"],
                check=True,
            )
            return
        except subprocess.CalledProcessError:
            pass

    if which("choco"):
        try:
            print("Installing OpenJDK via Chocolatey...")
            subprocess.run(["choco", "install", "-y", "temurin17"], check=True)
            return
        except subprocess.CalledProcessError:
            pass

    print("Error: neither winget nor choco found. Install Java manually from https://adoptium.net/")


def download_cfr():
    if os.path.isfile(CFR_JAR):
        return
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"Downloading CFR {CFR_VERSION}...")
    try:
        urllib.request.urlretrieve(CFR_URL, CFR_JAR)
    except Exception as e:
        print(f"Error downloading CFR: {e}")
        sys.exit(1)


def decompile(input_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Decompiling '{input_path}' -> '{output_dir}'")
    java_exe = which("java") or "java"
    result = subprocess.run(
        [java_exe, "-jar", CFR_JAR, input_path, "--outputdir", output_dir]
    )
    if result.returncode != 0:
        print(f"CFR exited with code {result.returncode}")


def find_nested_jars(root):
    nested = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(".jar"):
                nested.append(os.path.join(dirpath, f))
    return nested


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = [a for a in sys.argv[1:] if a.startswith("-")]

    recursive = "--recursive" in flags or "-r" in flags

    if not args:
        print("Usage: python decompile_jar.py <file.jar|file.class> [output_dir] [--recursive]")
        sys.exit(1)

    input_path = args[0]
    output_dir = args[1] if len(args) > 1 else None

    if not os.path.isfile(input_path):
        print(f"Error: '{input_path}' not found")
        sys.exit(1)

    ensure_java()
    download_cfr()

    # Default output: current working directory, named after the input file
    if not output_dir:
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.join(os.getcwd(), base + "-src")

    decompile(input_path, output_dir)

    if recursive:
        print("Scanning for nested JARs...")
        for nested in find_nested_jars(output_dir):
            nested_out = os.path.splitext(nested)[0] + "-src"
            print(f"  Decompiling nested: {nested}")
            decompile(nested, nested_out)

    print("Done.")


if __name__ == "__main__":
    main()