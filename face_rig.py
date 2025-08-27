import bpy
import addon_utils
import os

# --- USER SETTINGS ---
FBX_PATH = r"D:\Khadija uni courses\face_rig_project\input.fbx"
OUTPUT_PATH = r"D:\Khadija uni courses\face_rig_project\output_rigged_model.blend"

# --- STEP 1: Enable Rigify ---
addon_utils.enable("rigify", default_set=True, persistent=True)
print("✅ Rigify add-on enabled successfully!")

# --- STEP 2: Clear Scene ---
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    if obj.name in bpy.context.view_layer.objects:
        obj.select_set(True)
print(f"🔍 Objects to delete: {[obj.name for obj in bpy.context.selected_objects]}")
bpy.ops.object.delete(use_global=False)
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
bpy.ops.object.select_all(action='DESELECT')
if metarig.name in bpy.context.view_layer.objects:
    metarig.select_set(True)
    bpy.context.view_layer.objects.active = metarig
    bpy.ops.object.location_clear()
    bpy.ops.object.rotation_clear()
    bpy.ops.object.scale_clear()
else:
    raise RuntimeError(f"❌ Metarig '{metarig.name}' not in active view layer!")

# --- STEP 6: Switch to Edit Mode for Adjustments (optional) ---
bpy.ops.object.mode_set(mode='EDIT')
print("✏️ Adjust bones here if needed in UI mode...")
bpy.ops.object.mode_set(mode='OBJECT')

# --- STEP 7: Generate Rig from Metarig ---
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

# --- STEP 8: Ensure Rig is in Active View Layer ---
if rig.name not in bpy.context.view_layer.objects:
    print(f"⚠️ Rig '{rig.name}' not in active view layer, moving it...")
    active_collection = bpy.context.view_layer.active_layer_collection.collection
    active_collection.objects.link(rig)
    for coll in rig.users_collection:
        if coll != active_collection:
            coll.objects.unlink(rig)

# --- STEP 9: Hide Metarig ---
metarig.hide_set(True)
print("✅ Metarig hidden!")

# --- STEP 10: Parent Model to Rig ---
bpy.ops.object.select_all(action='DESELECT')
# Identify the imported mesh (assuming it's the first mesh after import)
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

# --- STEP 11: Save Rigged Model ---
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_PATH)
print(f"✅ Rigged model saved to: {OUTPUT_PATH}")

print("🎯 Face rigging complete!")