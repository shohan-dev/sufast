use crate::handlers::dynamic_handler;
use axum::{routing::any, Router};
use std::{
    net::{IpAddr, Ipv4Addr, SocketAddr},
    thread,
};
use tokio::{runtime::Runtime, net::TcpListener};

/// Starts the Axum server in a new thread
/// Returns true on success
pub fn start_server(production: bool, port: u16) -> bool {
    let port = if port == 1 { 8080 } else { port };

    let ip = if production {
        IpAddr::V4(Ipv4Addr::new(0, 0, 0, 0)) // public
    } else {
        IpAddr::V4(Ipv4Addr::new(127, 0, 0, 1)) // localhost
    };

    thread::spawn(move || {
        let rt = Runtime::new().expect("Failed to create Tokio runtime");
        rt.block_on(async move {
            let app = Router::new().fallback(any(dynamic_handler));
            let addr = SocketAddr::new(ip, port);

            println!("🚀 Server running at http://{}", addr);

            let listener = TcpListener::bind(addr).await.expect("Failed to bind to address");
            if let Err(err) = axum::serve(listener, app).await {
                eprintln!("❌ Server error: {}", err);
            }
        });
    });

    true
}
