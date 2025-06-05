import ctypes
import json
import platform
import warnings
import os
import sys

class App:
    def __init__(self):
        self.routes = {method: {} for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]}
        self.library_name = "sufast_server.dll" if platform.system() == "Windows" else "sufast_server.so"
        try:
            if sys.version_info >= (3, 9):
                from importlib.resources import files
                print("the libary name: ",self.library_name)
                self.dll_path = str(files("sufast").joinpath(self.library_name))
            else:
                import pkg_resources
                self.dll_path = pkg_resources.resource_filename("sufast", self.library_name)
        except Exception as e:
            raise RuntimeError(f"Could not resolve {self.library_name} location: {e}")

    def _load_sufast_lib(self):
        try:
            full_path = os.path.abspath(self.dll_path)
            print(f"🔍 Loading sufast library from: {full_path}")
            if platform.system() == "Linux":
                if not os.path.isfile(full_path):
                    raise FileNotFoundError(f"Linux .so file not found at: {full_path}")
                if not os.access(full_path, os.R_OK):
                    raise PermissionError(f"No read access to .so file: {full_path}")
            lib = ctypes.CDLL(full_path)
            lib.set_routes.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
            lib.set_routes.restype = ctypes.c_bool
            lib.start_server.argtypes = [ctypes.c_bool, ctypes.c_uint16]
            lib.start_server.restype = ctypes.c_bool
            return lib
        except OSError as e:
            raise ImportError(
                f"❌ Failed to load shared library at {full_path}:\n{str(e)}\n"
                "💡 Tips:\n"
                "  - Check the file exists and is readable\n"
                "  - Check 'ldd' output on Linux for missing dependencies\n"
                "  - Ensure Python and library architectures match (both 64-bit or 32-bit)\n"
                "  - Check file permissions\n"
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
