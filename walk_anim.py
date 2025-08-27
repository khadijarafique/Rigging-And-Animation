import bpy
import addon_utils
import os

# --- USER SETTINGS ---
FBX_PATH = r"D:\Khadija uni courses\face_rig_project\input.fbx"
OUTPUT_PATH = r"D:\Khadija uni courses\face_rig_project\output_rigged_model1.blend"

# --- STEP 1: Enable Rigify ---
addon_utils.enable("rigify", default_set=True, persistent=True)
print("✅ Rigify add-on enabled successfully!")

# --- STEP 2: Clear Scene ---
print(f"🔍 Initial objects in scene: {[obj.name for obj in bpy.data.objects]}")
for obj in bpy.data.objects:
    obj.select_set(False)  # Deselect all objects programmatically
for obj in bpy.data.objects:
    if obj.name in bpy.context.view_layer.objects:
        obj.select_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)  # Remove objects instead of using operator
print("✅ Scene cleared!")

# --- STEP 3: Import FBX ---
if os.path.exists(FBX_PATH):
    bpy.ops.import_scene.fbx(filepath=FBX_PATH)
    print(f"✅ Model loaded from: {FBX_PATH}")
else:
    raise FileNotFoundError(f"❌ FBX file not found at {FBX_PATH}")

# --- STEP 4: Add Human Metarig ---
bpy.ops.object.armature_human_metarig_add()
metarig = bpy.context.active_object
metarig.name = "Face_Metarig"
print("✅ Human metarig added!")

# --- STEP 5: Position Metarig at Model ---
bpy.ops.object.mode_set(mode='OBJECT')
for obj in bpy.data.objects:
    obj.select_set(False)  # Deselect all before setting active
if metarig.name in bpy.context.view_layer.objects:
    metarig.select_set(True)
    bpy.context.view_layer.objects.active = metarig
    bpy.ops.object.location_clear()
    bpy.ops.object.rotation_clear()
    bpy.ops.object.scale_clear()
else:
    raise RuntimeError(f"❌ Metarig '{metarig.name}' not in active view layer!")

# --- STEP 6: Generate Rig from Metarig ---
bpy.context.view_layer.objects.active = metarig
bpy.ops.pose.rigify_generate()
print("🔍 Checking for generated rig...")
rig = None
for obj in bpy.data.objects:
    if obj.type == "ARMATURE" and obj.name.startswith("RIG-Face_Metarig"):
        rig = obj
        break
if not rig:
    raise RuntimeError("❌ Generated rig not found! Check Rigify generation.")
print(f"✅ Rig generated: '{rig.name}'")

# --- STEP 7: Ensure Rig is in Active View Layer ---
if rig.name not in bpy.context.view_layer.objects:
    print(f"⚠️ Rig '{rig.name}' not in active view layer, moving it...")
    active_collection = bpy.context.view_layer.active_layer_collection.collection
    active_collection.objects.link(rig)
    for coll in rig.users_collection:
        if coll != active_collection:
            coll.objects.unlink(rig)

# --- STEP 8: Hide Metarig ---
metarig.hide_set(True)
print("✅ Metarig hidden!")

# --- STEP 9: Parent Model to Rig ---
for obj in bpy.data.objects:
    obj.select_set(False)  # Deselect all before parenting
mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name in bpy.context.view_layer.objects and not obj.name.startswith("WGT-")]
if not mesh_objects:
    raise RuntimeError("❌ No mesh objects found in active view layer!")
print(f"🔍 All objects in scene: {[obj.name for obj in bpy.data.objects]}")
print(f"🔍 Mesh objects in view layer: {[obj.name for obj in mesh_objects]}")
for obj in mesh_objects:
    print(f"🔍 Selecting mesh: {obj.name}")
    obj.select_set(True)
if rig.name in bpy.context.view_layer.objects:
    print(f"🔍 Activating rig: {rig.name}")
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    print("✅ Model parented to rig successfully!")
else:
    raise RuntimeError(f"❌ Rig '{rig.name}' not in active view layer!")

# --- STEP 10: Create Standing Pose and Walking Animation ---
print("🔍 Creating standing pose and walking animation...")
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 48  # 48 frames for smooth walk cycle

# Switch to Pose Mode
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')

# Debug: Print available bone names
print(f"🔍 Available bone names: {[bone.name for bone in rig.pose.bones]}")

# Map expected bone names to actual names based on availability
bones = rig.pose.bones
bone_map = {
    "thigh.L": next((b for b in bones if "thigh.L" in b.name and b.name.startswith("DEF-")), None),
    "thigh.R": next((b for b in bones if "thigh.R" in b.name and b.name.startswith("DEF-")), None),
    "shin.L": next((b for b in bones if "shin.L" in b.name and b.name.startswith("DEF-")), None),
    "shin.R": next((b for b in bones if "shin.R" in b.name and b.name.startswith("DEF-")), None),
    "upper_arm.L": next((b for b in bones if "upper_arm.L" in b.name and b.name.startswith("DEF-")), None),
    "upper_arm.R": next((b for b in bones if "upper_arm.R" in b.name and b.name.startswith("DEF-")), None),
    "spine.001": next((b for b in bones if "spine.001" in b.name and b.name.startswith("DEF-")), None),
    "root": next((b for b in bones if b.name == "root"), None)
}

# Check if all required bones are found
missing_bones = [name for name, bone in bone_map.items() if bone is None]
if missing_bones:
    print(f"⚠️ Warning: Missing bones: {missing_bones}. Animation may be incomplete. Check '🔍 Available bone names:' output.")
else:
    print("✅ All required bones found!")

# Set neutral upright standing pose at frame 1
for bone in bones:
    bone.rotation_euler = (0, 0, 0)
    bone.location = (0, 0, 0)
if bone_map["thigh.L"]: bone_map["thigh.L"].rotation_euler = (0, 0, 0)  # Straight legs
if bone_map["thigh.R"]: bone_map["thigh.R"].rotation_euler = (0, 0, 0)
if bone_map["shin.L"]: bone_map["shin.L"].rotation_euler = (0, 0, 0)  # Straight shins
if bone_map["shin.R"]: bone_map["shin.R"].rotation_euler = (0, 0, 0)
if bone_map["upper_arm.L"]: bone_map["upper_arm.L"].rotation_euler = (-0.2, -0.3, 0)  # Arm down and slightly forward
if bone_map["upper_arm.R"]: bone_map["upper_arm.R"].rotation_euler = (-0.2, 0.3, 0)  # Arm down and slightly forward
if bone_map["spine.001"]: bone_map["spine.001"].rotation_euler = (0, 0, 0)  # Upright spine
if bone_map["root"]: bone_map["root"].location = (0, 0, 0)  # Grounded position
if bone_map["thigh.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['thigh.L'].name}\"].rotation_euler", frame=1)
if bone_map["thigh.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['thigh.R'].name}\"].rotation_euler", frame=1)
if bone_map["shin.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['shin.L'].name}\"].rotation_euler", frame=1)
if bone_map["shin.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['shin.R'].name}\"].rotation_euler", frame=1)
if bone_map["upper_arm.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['upper_arm.L'].name}\"].rotation_euler", frame=1)
if bone_map["upper_arm.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['upper_arm.R'].name}\"].rotation_euler", frame=1)
if bone_map["spine.001"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['spine.001'].name}\"].rotation_euler", frame=1)
if bone_map["root"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['root'].name}\"].location", frame=1)

# Keyframe walking cycle starting from standing pose
try:
    # Frame 12: Left leg forward, right leg back
    bpy.context.scene.frame_set(12)
    if bone_map["thigh.L"]: bone_map["thigh.L"].rotation_euler = (0.5, 0, 0)  # Forward bend
    if bone_map["thigh.R"]: bone_map["thigh.R"].rotation_euler = (-0.3, 0, 0)  # Backward bend
    if bone_map["shin.L"]: bone_map["shin.L"].rotation_euler = (-0.2, 0, 0)  # Knee bend
    if bone_map["shin.R"]: bone_map["shin.R"].rotation_euler = (0.1, 0, 0)  # Slight knee bend
    if bone_map["upper_arm.L"]: bone_map["upper_arm.L"].rotation_euler = (-0.2, -0.5, 0)  # Left arm back
    if bone_map["upper_arm.R"]: bone_map["upper_arm.R"].rotation_euler = (-0.2, 0.5, 0)  # Right arm forward
    if bone_map["spine.001"]: bone_map["spine.001"].rotation_euler = (0, 0, 0.1)  # Upper spine twist
    if bone_map["root"]: bone_map["root"].location = (0.1, 0, 0)  # Forward movement
    if bone_map["thigh.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['thigh.L'].name}\"].rotation_euler", frame=12)
    if bone_map["thigh.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['thigh.R'].name}\"].rotation_euler", frame=12)
    if bone_map["shin.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['shin.L'].name}\"].rotation_euler", frame=12)
    if bone_map["shin.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['shin.R'].name}\"].rotation_euler", frame=12)
    if bone_map["upper_arm.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['upper_arm.L'].name}\"].rotation_euler", frame=12)
    if bone_map["upper_arm.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['upper_arm.R'].name}\"].rotation_euler", frame=12)
    if bone_map["spine.001"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['spine.001'].name}\"].rotation_euler", frame=12)
    if bone_map["root"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['root'].name}\"].location", frame=12)

    # Frame 24: Left leg mid-stance, right leg lifting
    bpy.context.scene.frame_set(24)
    if bone_map["thigh.L"]: bone_map["thigh.L"].rotation_euler = (0.1, 0, 0)
    if bone_map["thigh.R"]: bone_map["thigh.R"].rotation_euler = (0.2, 0, 0)
    if bone_map["shin.L"]: bone_map["shin.L"].rotation_euler = (0, 0, 0)
    if bone_map["shin.R"]: bone_map["shin.R"].rotation_euler = (-0.2, 0, 0)
    if bone_map["upper_arm.L"]: bone_map["upper_arm.L"].rotation_euler = (-0.2, -0.3, 0)
    if bone_map["upper_arm.R"]: bone_map["upper_arm.R"].rotation_euler = (-0.2, 0.3, 0)
    if bone_map["spine.001"]: bone_map["spine.001"].rotation_euler = (0, 0, 0.05)
    if bone_map["root"]: bone_map["root"].location = (0.2, 0, 0)
    if bone_map["thigh.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['thigh.L'].name}\"].rotation_euler", frame=24)
    if bone_map["thigh.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['thigh.R'].name}\"].rotation_euler", frame=24)
    if bone_map["shin.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['shin.L'].name}\"].rotation_euler", frame=24)
    if bone_map["shin.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['shin.R'].name}\"].rotation_euler", frame=24)
    if bone_map["upper_arm.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['upper_arm.L'].name}\"].rotation_euler", frame=24)
    if bone_map["upper_arm.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['upper_arm.R'].name}\"].rotation_euler", frame=24)
    if bone_map["spine.001"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['spine.001'].name}\"].rotation_euler", frame=24)
    if bone_map["root"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['root'].name}\"].location", frame=24)

    # Frame 36: Right leg forward, left leg back
    bpy.context.scene.frame_set(36)
    if bone_map["thigh.L"]: bone_map["thigh.L"].rotation_euler = (-0.3, 0, 0)
    if bone_map["thigh.R"]: bone_map["thigh.R"].rotation_euler = (0.5, 0, 0)
    if bone_map["shin.L"]: bone_map["shin.L"].rotation_euler = (0.1, 0, 0)
    if bone_map["shin.R"]: bone_map["shin.R"].rotation_euler = (-0.2, 0, 0)
    if bone_map["upper_arm.L"]: bone_map["upper_arm.L"].rotation_euler = (-0.2, 0.5, 0)
    if bone_map["upper_arm.R"]: bone_map["upper_arm.R"].rotation_euler = (-0.2, -0.5, 0)
    if bone_map["spine.001"]: bone_map["spine.001"].rotation_euler = (0, 0, -0.1)
    if bone_map["root"]: bone_map["root"].location = (0.3, 0, 0)
    if bone_map["thigh.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['thigh.L'].name}\"].rotation_euler", frame=36)
    if bone_map["thigh.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['thigh.R'].name}\"].rotation_euler", frame=36)
    if bone_map["shin.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['shin.L'].name}\"].rotation_euler", frame=36)
    if bone_map["shin.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['shin.R'].name}\"].rotation_euler", frame=36)
    if bone_map["upper_arm.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['upper_arm.L'].name}\"].rotation_euler", frame=36)
    if bone_map["upper_arm.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['upper_arm.R'].name}\"].rotation_euler", frame=36)
    if bone_map["spine.001"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['spine.001'].name}\"].rotation_euler", frame=36)
    if bone_map["root"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['root'].name}\"].location", frame=36)

    # Frame 48: Right leg mid-stance, left leg lifting
    bpy.context.scene.frame_set(48)
    if bone_map["thigh.L"]: bone_map["thigh.L"].rotation_euler = (-0.1, 0, 0)
    if bone_map["thigh.R"]: bone_map["thigh.R"].rotation_euler = (0.1, 0, 0)
    if bone_map["shin.L"]: bone_map["shin.L"].rotation_euler = (-0.2, 0, 0)
    if bone_map["shin.R"]: bone_map["shin.R"].rotation_euler = (0, 0, 0)
    if bone_map["upper_arm.L"]: bone_map["upper_arm.L"].rotation_euler = (-0.2, 0.3, 0)
    if bone_map["upper_arm.R"]: bone_map["upper_arm.R"].rotation_euler = (-0.2, -0.3, 0)
    if bone_map["spine.001"]: bone_map["spine.001"].rotation_euler = (0, 0, -0.05)
    if bone_map["root"]: bone_map["root"].location = (0.4, 0, 0)
    if bone_map["thigh.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['thigh.L'].name}\"].rotation_euler", frame=48)
    if bone_map["thigh.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['thigh.R'].name}\"].rotation_euler", frame=48)
    if bone_map["shin.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['shin.L'].name}\"].rotation_euler", frame=48)
    if bone_map["shin.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['shin.R'].name}\"].rotation_euler", frame=48)
    if bone_map["upper_arm.L"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['upper_arm.L'].name}\"].rotation_euler", frame=48)
    if bone_map["upper_arm.R"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['upper_arm.R'].name}\"].rotation_euler", frame=48)
    if bone_map["spine.001"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['spine.001'].name}\"].rotation_euler", frame=48)
    if bone_map["root"]: rig.keyframe_insert(data_path=f"pose.bones[\"{bone_map['root'].name}\"].location", frame=48)

except Exception as e:
    print(f"❌ Error: {e}. Check bone names in the rig.")

# Return to Object Mode
bpy.ops.object.mode_set(mode='OBJECT')
print("✅ Standing pose and walking animation created!")

# --- STEP 11: Save Rigged Model ---
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_PATH)
print(f"✅ Rigged model saved to: {OUTPUT_PATH}")

print("🎯 Face rigging and walking animation complete!")