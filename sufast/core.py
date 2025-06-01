import ctypes
import json
import warnings
import os
import sys

class App:
    def __init__(self):
        self.routes = {method: {} for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]}

        try:
            if sys.version_info >= (3, 9):
                from importlib.resources import files
                self.dll_path = str(files("sufast").joinpath("sufast_server.dll"))
            else:
                import pkg_resources
                self.dll_path = pkg_resources.resource_filename("sufast", "sufast_server.dll")
        except Exception as e:
            raise RuntimeError(f"Could not resolve sufast_server.dll location: {e}")

    def _load_sufast_lib(self):
        try:
            lib = ctypes.CDLL(os.path.abspath(self.dll_path))
            lib.set_routes.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
            lib.set_routes.restype = ctypes.c_bool
            lib.start_server.argtypes = [ctypes.c_bool, ctypes.c_uint16]
            lib.start_server.restype = ctypes.c_bool
            return lib
        except OSError as e:
            raise ImportError(
                # f"❌ Failed to load sufast_server.dll at {self.dll_path}: {str(e)}\n"
                "💡 Note: This Framework is currently only supported on Windows operating systems.\n"
                "   Please check: 1) file exists  2) Architecture compatibility (32/64-bit)  3) Required dependencies are installed"
            ) from e

    def _register(self, method, path, handler):
        try:
            result = handler()
            self.routes[method][path] = json.dumps(result) if not isinstance(result, str) else result
        except Exception as e:
            error_msg = f"⚠️ Handler error for {method} {path}: {e}"
            self.routes[method][path] = json.dumps({"error": error_msg})
            warnings.warn(error_msg)

    def get(self, path): return self._decorator("GET", path)
    def post(self, path): return self._decorator("POST", path)
    def put(self, path): return self._decorator("PUT", path)
    def patch(self, path): return self._decorator("PATCH", path)
    def delete(self, path): return self._decorator("DELETE", path)

    def _decorator(self, method, path):
        def decorator(func):
            self._register(method, path, func)
            return func
        return decorator

    def run(self, port=8080, production=False):
        lib = self._load_sufast_lib()
        json_routes = json.dumps(self.routes).encode('utf-8')
        buffer = (ctypes.c_ubyte * len(json_routes)).from_buffer_copy(json_routes)

        print("\n🔧 Booting up ⚡ sufast web server engine...\n")
        print(f"🌐 Mode     : {'🔒 Production' if production else '🧪 Development'}")
        print(f"🔀  Routes   : {sum(len(r) for r in self.routes.values())} registered")
        print(f"🚪 Port     : {port}")
        print("🟢 Status   : Server is up and running!")
        if not production:
            print(f"➡️  Visit    : http://localhost:{port}")
        print("🔄 Press Ctrl+C to stop the server.\n")

        if not lib.set_routes(buffer, len(json_routes)):
            raise RuntimeError("❌ sufast_server failed to accept route configuration.")

        if not lib.start_server(production, port):
            raise RuntimeError("❌ sufast_server failed to start.") 

        try:
            while True:
                pass
        except KeyboardInterrupt:
            print("🛑 Server stopped by user.")
        except Exception as e:
            print(f"🔥 Unexpected error: {str(e)}")
