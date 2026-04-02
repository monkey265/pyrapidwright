import os
import jpype
import jpype.imports
from pathlib import Path

def get_rw_path():
    """Returns the discovered RapidWright path."""
    import os
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent.absolute()
    
    rw_path = os.environ.get("RAPIDWRIGHT_PATH")
    if not rw_path:
        local_rw = project_root / "rapidwright"
        if local_rw.exists():
            rw_path = str(local_rw)
        else:
            rw_path = "/home/pepa/work/RapidWright/RapidWright" # Fallback
            
    return Path(rw_path)

def setup_rw(rw_path=None):
    """Initializes the JVM with the RapidWright classpath."""
    if jpype.isJVMStarted():
        return

    if not rw_path:
        rw_path = str(get_rw_path())
            
    rw_root = Path(rw_path)
    if not rw_root.exists():
        raise FileNotFoundError(f"RapidWright not found at {rw_path}. Please set RAPIDWRIGHT_PATH.")

    # Build Classpath: bin + all jars
    # Note: Using wildcard classpath for convenience in JPype
    if not jpype.isJVMStarted():
        jpype.startJVM(jpype.getDefaultJVMPath(), "-ea", f"-Djava.class.path={rw_path}/bin:{rw_path}/bin/*:{rw_path}/jars/*")
    
    print(f"[*] RapidWright JVM Started (Path: {rw_path})")

# Auto-initialize if environmental variable is set
if "RAPIDWRIGHT_PATH" in os.environ:
    setup_rw()
elif (Path(__file__).parent.parent / "rapidwright").exists():
    setup_rw()
else:
    # Optional: don't auto-initialize if not found
    pass