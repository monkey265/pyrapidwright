import os
import jpype
import jpype.imports
from pathlib import Path

def get_rw_path():
    """Returns $RAPIDWRIGHT_PATH, or ./rapidwright next to the package (where install_rapidwright.sh puts it)."""
    return Path(os.environ.get("RAPIDWRIGHT_PATH") or Path(__file__).parent.parent.absolute() / "rapidwright")

def setup_rw(rw_path=None):
    """Initializes the JVM with the RapidWright classpath. Safe to call repeatedly."""
    if jpype.isJVMStarted():
        return

    rw_path = str(rw_path or get_rw_path())
    if not Path(rw_path).exists():
        raise FileNotFoundError(f"RapidWright not found at {rw_path}. Run install_rapidwright.sh or set RAPIDWRIGHT_PATH.")

    # Build Classpath: bin + all jars
    jpype.startJVM(jpype.getDefaultJVMPath(), "-ea", f"-Djava.class.path={rw_path}/bin:{rw_path}/bin/*:{rw_path}/jars/*")
    print(f"[*] RapidWright JVM Started (Path: {rw_path})")
