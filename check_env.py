import sys
import os # For checking PYTHONPATH

print("--- Environment Info ---")
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")

print("\n--- PYTHONPATH Environment Variable ---")
pythonpath_env = os.getenv('PYTHONPATH')
if pythonpath_env:
    print(f"PYTHONPATH is SET: {pythonpath_env}")
    print("PYTHONPATH individual entries (split by os.pathsep):")
    for p_entry in pythonpath_env.split(os.pathsep):
        print(f"  - {p_entry}")
else:
    print("PYTHONPATH is NOT SET or is EMPTY.")

print("\n--- sys.path (Module Search Path) ---")
# Printing only the first few and site-packages for brevity, add more if needed
print("First few sys.path entries:")
for i, p in enumerate(sys.path):
    if i < 5: # Print first 5
        print(f"  - {p}")
    if 'site-packages' in p:
        print(f"  - {p} (potential site-packages directory)")
if len(sys.path) > 5 and not any('site-packages' in p for p in sys.path[:5]):
    print("  - ... (other non-site-packages paths) ...")


print("\n--- Discord.py Import Test ---")
try:
    import discord
    print(f"Successfully imported 'discord' module.")
    # These two lines are CRITICAL:
    print(f"discord.__version__ (reported by imported module): {discord.__version__}")
    print(f"discord.__file__ (location of imported module): {discord.__file__}")

    # Now, try to access discord.sinks
    print("\nAttempting to access discord.sinks...")
    if hasattr(discord, 'sinks'):
        print("discord.sinks IS ACCESSIBLE.")
        # print(f"discord.sinks object: {discord.sinks}") # Can be verbose
    else:
        print("discord.sinks IS NOT ACCESSIBLE (module 'discord' has no attribute 'sinks').")

except ImportError as e_import:
    print(f"ImportError: Failed to import 'discord'. Error: {e_import}")
    print("Ensure discord.py is installed in the correct Python environment that this script is using.")
except AttributeError as e_attr:
    print(f"AttributeError encountered: {e_attr}")
    # Try to print version and file anyway if discord object exists but accessing attributes failed early
    if 'discord' in locals() and hasattr(discord, '__version__') and hasattr(discord, '__file__'):
        print(f"(Fallback attempt) discord.__version__: {discord.__version__}")
        print(f"(Fallback attempt) discord.__file__: {discord.__file__}")
    else:
        print("(Fallback attempt) Could not get version/file info after AttributeError.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")