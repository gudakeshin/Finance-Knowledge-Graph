#!/usr/bin/env python3

import sys
import traceback
sys.path.append('backend')

try:
    from routers.process import router
    print("Router loaded successfully")
    print(f"Number of routes: {len(router.routes)}")
    for route in router.routes:
        print(f"{route.methods} {route.path}")
except Exception as e:
    print(f"Error loading router: {e}")
    traceback.print_exc() 