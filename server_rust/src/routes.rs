use axum::http::Method;
use once_cell::sync::OnceCell;
use std::{
    collections::HashMap,
    sync::{Arc, RwLock},
};

/// InnerRoutes: path -> response body (JSON string)
pub type InnerRoutes = HashMap<String, String>;

/// SharedRoutes: method -> InnerRoutes
pub type SharedRoutes = Arc<RwLock<HashMap<Method, InnerRoutes>>>;

static ROUTES: OnceCell<SharedRoutes> = OnceCell::new();

/// Set routes (overwrites all current routes).
/// Call this from FFI or Python interface with parsed JSON string data.
pub fn set_static_routes(new_routes: HashMap<Method, InnerRoutes>) -> bool {
    if ROUTES
        .set(Arc::new(RwLock::new(new_routes.clone())))
        .is_err()
    {
        // If already initialized, update the map in-place
        if let Some(routes) = ROUTES.get() {
            if let Ok(mut write_guard) = routes.write() {
                *write_guard = new_routes;
                return true;
            }
        }
        return false;
    }
    true
}

/// Get reference to shared routes (for handler)
pub fn get_routes() -> Option<&'static SharedRoutes> {
    ROUTES.get()
}
