use axum::http::Method;
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use std::collections::HashMap;
use sufast_core::handlers::match_path;
use sufast_core::routes::set_static_routes;

fn benchmark_route_matching(c: &mut Criterion) {
    c.bench_function("static route match", |b| {
        b.iter(|| match_path(black_box("/users"), black_box("/users")))
    });

    c.bench_function("dynamic route match", |b| {
        b.iter(|| match_path(black_box("/users/{id}"), black_box("/users/123")))
    });

    c.bench_function("complex dynamic route match", |b| {
        b.iter(|| {
            match_path(
                black_box("/api/v1/users/{user_id}/posts/{post_id}/comments/{comment_id}"),
                black_box("/api/v1/users/123/posts/456/comments/789"),
            )
        })
    });
}

fn benchmark_route_storage(c: &mut Criterion) {
    c.bench_function("store 100 routes", |b| {
        b.iter(|| {
            let mut routes = HashMap::new();
            let mut get_routes = HashMap::new();

            for i in 0..100 {
                get_routes.insert(format!("/route{}", i), format!(r#"{{"id": {}}}"#, i));
            }

            routes.insert(Method::GET, get_routes);
            set_static_routes(black_box(routes))
        })
    });

    c.bench_function("store 1000 routes", |b| {
        b.iter(|| {
            let mut routes = HashMap::new();
            let mut get_routes = HashMap::new();

            for i in 0..1000 {
                get_routes.insert(format!("/route{}", i), format!(r#"{{"id": {}}}"#, i));
            }

            routes.insert(Method::GET, get_routes);
            set_static_routes(black_box(routes))
        })
    });
}

criterion_group!(benches, benchmark_route_matching, benchmark_route_storage);
criterion_main!(benches);
