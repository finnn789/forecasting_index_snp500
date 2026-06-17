c = get_config()  # noqa: F821

# --- Server ---
c.ServerApp.port = 8888
c.ServerApp.ip = "127.0.0.1"
c.ServerApp.open_browser = False
c.ServerApp.root_dir = "."
c.ServerApp.notebook_dir = "notebooks"
c.IdentityProvider.token = "19855f00b6c4ea36df979cf65b8cee836672592058bf70f4"
c.ServerApp.password = ""

# --- Kernel default ---
c.MultiKernelManager.default_kernel_name = "stock-prediction"

# --- Rate limit (supaya output DataFrame besar tidak hang) ---
c.ZMQChannelsWebsocketConnection.iopub_data_rate_limit = 10_000_000
c.ZMQChannelsWebsocketConnection.iopub_msg_rate_limit = 3_000

# --- WebSocket settings (untuk MCP + koneksi kernel yang stabil) ---
c.ServerApp.websocket_ping_interval = 30000  # ms
c.ServerApp.websocket_ping_timeout = 30000   # harus <= ping_interval
