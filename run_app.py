import sys
import asyncio
from streamlit.web import cli

if __name__ == "__main__":
    # Manually create and set the asyncio event loop to patch the Python 3.14 behavior
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    
    # Override sys.argv to simulate running `streamlit run app.py`
    sys.argv = ["streamlit", "run", "app.py"]
    
    # Start Streamlit CLI
    sys.exit(cli.main())