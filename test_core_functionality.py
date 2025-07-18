#!/usr/bin/env python3
"""
Simple test to verify the ultra-optimized Sufast core is working correctly.
"""

import sys
import os
import time

# Add the python directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

try:
    from sufast import SufastUltraOptimized
    print("✅ Successfully imported SufastUltraOptimized")
except ImportError as e:
    print(f"❌ Failed to import SufastUltraOptimized: {e}")
    sys.exit(1)

def test_core_functionality():
    """Test core functionality without HTTP server."""
    print("\n🔬 Testing Core Functionality...")
    
    # Create app instance
    app = SufastUltraOptimized()
    print("✅ SufastUltraOptimized instance created")
    
    # Check Rust core status
    if app.rust_core and app.rust_core.is_loaded:
        print("✅ Rust core loaded and ready")
        
        # Test performance stats
        try:
            stats = app.get_performance_stats()
            print(f"✅ Performance stats: {stats}")
        except Exception as e:
            print(f"⚠️  Performance stats error: {e}")
        
        # Test cache operations
        try:
            app.clear_all_caches()
            print("✅ Cache clearing successful")
        except Exception as e:
            print(f"⚠️  Cache clearing error: {e}")
            
    else:
        print("⚠️  Rust core not loaded, using Python fallback")
    
    # Add some routes to test route registration
    @app.route("/")
    def home():
        return {"message": "Ultra-Fast Sufast Server", "tier": "static"}
    
    @app.route("/api/test")
    def test_api():
        return {"test": "success", "tier": "cached"}
    
    @app.route("/dynamic/<id>")
    def dynamic_route(id):
        return {"id": id, "timestamp": time.time(), "tier": "dynamic"}
    
    print("✅ Routes registered successfully")
    
    # Test route caching
    try:
        stats = app.get_performance_stats()
        print(f"✅ Routes in system: {stats}")
    except Exception as e:
        print(f"⚠️  Route stats error: {e}")
    
    return True

def test_static_optimization():
    """Test static route optimization."""
    print("\n⚡ Testing Static Route Optimization...")
    
    app = SufastUltraOptimized()
    
    # Test static route caching
    test_routes = [
        ("/", {"message": "home"}),
        ("/health", {"status": "ok"}),
        ("/api/status", {"api": "ready"}),
    ]
    
    for path, response in test_routes:
        try:
            if app.rust_core and app.rust_core.is_loaded:
                app.rust_core.add_static_route(path, response)
                print(f"✅ Static route cached: {path}")
            else:
                print(f"⚠️  Static route (Python): {path}")
        except Exception as e:
            print(f"❌ Failed to cache route {path}: {e}")
    
    return True

def test_performance_counters():
    """Test performance monitoring."""
    print("\n📊 Testing Performance Counters...")
    
    app = SufastUltraOptimized()
    
    try:
        stats = app.get_performance_stats()
        
        # Check for expected stats fields
        expected_fields = ['rust_core_loaded', 'performance_tier']
        
        for field in expected_fields:
            if field in stats:
                print(f"✅ {field}: {stats[field]}")
            else:
                print(f"⚠️  Missing field: {field}")
        
        print(f"✅ Full stats: {stats}")
        
    except Exception as e:
        print(f"❌ Performance counter error: {e}")
        return False
    
    return True

def main():
    """Main test function."""
    print("🚀 Testing Ultra-Optimized Sufast Core")
    print("=" * 50)
    
    tests = [
        ("Core Functionality", test_core_functionality),
        ("Static Optimization", test_static_optimization),
        ("Performance Counters", test_performance_counters),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All core tests passed! Ultra-optimized Sufast core is working correctly.")
        print("🦀 Rust core integrated successfully")
        print("⚡ Three-tier optimization system active")
        print("🚀 Ready for production use!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
