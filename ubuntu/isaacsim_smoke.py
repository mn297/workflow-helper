import traceback
from isaacsim import SimulationApp

app = SimulationApp({"headless": True})
print("STAGE1_APP_STARTED", flush=True)

rc = 1
try:
    import numpy as np
    import isaacsim.core.experimental.utils.stage as stage_utils
    from isaacsim.core.experimental.objects import Cube, GroundPlane
    from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
    from isaacsim.core.simulation_manager import SimulationManager
    print("STAGE2_IMPORTS_OK", flush=True)

    stage_utils.create_new_stage()
    print("STAGE3_STAGE_OK", flush=True)

    GroundPlane("/World/ground")
    Cube(paths="/World/cube", sizes=[[0.5, 0.5, 0.5]], positions=[[0.0, 0.0, 2.0]])
    GeomPrim(paths="/World/cube", apply_collision_apis=True)
    body = RigidPrim(paths="/World/cube", masses=[1.0])
    print("STAGE4_SCENE_OK", flush=True)

    SimulationManager.setup_simulation(dt=1.0 / 60.0)
    import omni.timeline
    tl = omni.timeline.get_timeline_interface()
    tl.play()
    for _ in range(150):
        app.update()
    pos, _ = body.get_world_poses()
    z = float(np.asarray(pos)[0][2])
    tl.stop()
    print(f"STAGE5_PHYSICS_OK final_z={z:.4f}", flush=True)
    # cube half-height 0.25 -> should rest near z=0.25 after falling from 2.0
    print("PHYSICS_PLAUSIBLE" if 0.1 < z < 0.45 else f"PHYSICS_SUSPECT z={z}", flush=True)
    rc = 0
except Exception:
    traceback.print_exc()
    print("SMOKE_FAILED", flush=True)
finally:
    app.close()
    print(f"SMOKE_RC={rc}", flush=True)
