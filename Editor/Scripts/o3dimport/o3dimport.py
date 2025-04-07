"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

# Created by Galib Arrieta (aka galibzon@github, lumbermixalot@github)
# under contract with Meta Platforms, Inc.
# Donated by Meta Platforms, Inc as an open source project.

import argparse
import json
import math
import os
import time
import ctypes

import azlmbr.asset as azasset

import azlmbr.bus as azbus
import azlmbr.components as azcomponents
import azlmbr.editor as azeditor
import azlmbr.entity as azentity
import azlmbr.legacy.general as azgeneral
import azlmbr.math as azmath
import azlmbr.render as azrender

# C:\GIT\o3de\AutomatedTesting\Gem\PythonTests\EditorPythonTestTools\editor_python_test_tools\editor_entity_utils.py
from editor_python_test_tools.editor_entity_utils import EditorComponent, EditorEntity

VERBOSE = False

# standard name for some components.
# CN_ stands for Component Name
CN_MESH = "Mesh"
CN_MATERIAL = "Material"
CN_NONUNIFORM_SCALE = "NonUniformScale"


def DumpEditorComponentProperties(editorComponent: EditorComponent):
    """
    A helper function to print all properties of a component.
    """
    props = editorComponent.get_property_type_visibility()
    for key, value in props.items():
        print(f"{key}: {value}")


def DumpComponentProperties(entityObj: EditorEntity, componentName: str):
    if not entityObj.has_component(componentName):
        print(
            f"Entity with id '{entityObj.id}' doesn't have component named '{componentName}'"
        )
        return
    componentList = entityObj.get_components_of_type(
        [
            componentName,
        ]
    )
    for editorComponent in componentList:
        DumpEditorComponentProperties(editorComponent)


def WaitUntilTrue(
    predicateFunction,
    timeoutInSeconds: float = 1.0,
    frameCountPolling: int = 1,
    verbose=False,
) -> bool:
    """
    A helper function that runs a predicate until it returns True.
    Each polling iteration yields to the Editor main thread for frameCountPolling number of frames.
    @returns True if the predicate returned true before @timeoutInSeconds.
    """
    endTime = time.time() + timeoutInSeconds
    tryCount = 0
    while True:
        if predicateFunction():
            return True
        if verbose:
            print(f"WaitUntilTrue: predicate failed at '{tryCount}' tryCount(s)")
        tryCount += 1
        try:
            azgeneral.idle_wait_frames(frameCountPolling)
        except Exception:
            print(f"WARNING: Couldn't wait for {frameCountPolling} frame(s)")
        if time.time() > endTime:  # timed out
            return False


class AssetPaths:
    def __init__(self, sceneName: str):
        gamePath = azeditor.EditorToolsApplicationRequestBus(
            azbus.Broadcast, "GetGameFolder"
        )
        self._relSceneDirectory = os.path.join("Assets", "Scenes", sceneName)
        self._absSceneGraphPath = os.path.join(
            gamePath, self._relSceneDirectory, f"{sceneName}.sgr"
        )

    def GetSceneGraphAbsolutePath(self) -> str:
        return self._absSceneGraphPath

    def GetMeshAssetProductPath(self, meshName: str) -> str:
        product_folder = os.path.join(self._relSceneDirectory, "Meshes")
        product_path = os.path.join(product_folder, f"{meshName}.fbx.azmodel")
        return product_path

    def GetMaterialAssetProductPath(self, materialName: str) -> str:
        product_folder = os.path.join(self._relSceneDirectory, "Materials")
        product_path = os.path.join(product_folder, f"{materialName}.azmaterial")
        return product_path


class EntityData:
    def __init__(self, name: str, editorEntity: EditorEntity, parentName: str, sceneGraphData: dict):
        self.name : str = name
        self.editorEntity : EditorEntity = editorEntity
        self.parentName : str = parentName
        self.sceneGraphData : dict = sceneGraphData
        self.meshComponent : EditorComponent = None # Optional. Will be filled later if the entity requires a Mesh component.
        self.materialComponent : EditorComponent = None # Optional. Will be filled later if the entity requires a Material component.


class SceneImporter:
    def __init__(
        self, assetPaths: AssetPaths, saveRate: int, sceneGraphDictionary: dict
    ):
        self._assetPaths = assetPaths
        self._saveRate = saveRate
        self._sceneGraph = sceneGraphDictionary
        self._addedEntities = 0
        self._processedEntities = 0
        # As we add or find entities in the scene, they are added here with key
        # being their name, and the value is an EntityData object
        # CAVEAT: Although O3DE accepts entities with the same name, most DCC tools, Blender
        # being one of them, do not allow same name for different entities. So it works
        # well to organize them in a dictionary by name.
        self._entitiesByName = {}

    def _BeginBatch(self):
        azeditor.ToolsApplicationRequestBus(
            azbus.Broadcast, "BeginUndoBatch", "Modify entities"
        )

    def _EndBatch(self):
        azeditor.ToolsApplicationRequestBus(azbus.Broadcast, "EndUndoBatch")

    def _OnEntityWasProcessed(self, entityName: str):
        self._processedEntities += 1
        print(f"Processed Entity '{entityName}' at count '{self._processedEntities}'")
        self._OnBatchSync()

    def _OnEntityWasCreated(self, entityName: str):
        self._addedEntities += 1
        print(f"Added Entity '{entityName}' at count '{self._addedEntities}'")
        self._OnBatchSync()

    def _OnBatchSync(self):
        total = self._processedEntities + self._addedEntities
        if (self._saveRate > 0) and (total % self._saveRate) == 0:
            self._EndBatch()
            azgeneral.save_level()
            self._BeginBatch()

    def _ResetCounters(self):
        self._processedEntities = 0
        self._addedEntities = 0

    def ImportScene(self):
        """
        Imports the whole scene in several recursive phases.
        Phase 1: Adds the entities and their children entities.
        Phase 2: Adds the NonUniformScale component, and sets the value of the transform componentes on all added entities.
        Phase 3: Adds the Mesh and the Material components to all entities that need it.
        Phase 4: Sets the mesh asset to all entities with Mesh component. Waits at least 2 frames after each asset is set.
        Phase 5: Sets the Material Asset to all MaterialSlots. For each entities waits at least 2 frames after all material slots have been set.
        """
        measured_times = [] # Will help get a total time spent.
        start_time = time.time()
        entitiesToAdd = self._sceneGraph["children"]
        sceneName = self._sceneGraph["name"]
        if len(entitiesToAdd) < 1:
            print(f"The SceneGraph '{sceneName}' is empty. Nothing to do.")
            return
        
        # Phase 1: Adds the entities and their children entities.
        self._BeginBatch()
        countOfNewEntities = self._AddEntitiesRecursive(
            parentEntityName="", parentEditorEntity=EditorEntity(azentity.EntityId()) , entities=entitiesToAdd
        )
        # Let's wait one second to let the UI refresh.
        azgeneral.idle_wait(1.0)
        self._EndBatch()
        azgeneral.save_level()
        elapsed_time = time.time() - start_time
        measured_times.append(elapsed_time)
        print(f"Phase 1. Duration: {elapsed_time} seconds.\nAdded {countOfNewEntities} new entities.\nTotal entities in the scene={len(self._entitiesByName)}.")

        # Phase 2: Sets the value of the transform componentes on all entities. Adds the NonUniformScale component for those who need it.
        self._BeginBatch()
        start_time = time.time()
        self._UpdateTransformComponentForAllEntities()
        azgeneral.idle_wait(1.0)
        self._EndBatch()
        azgeneral.save_level()
        elapsed_time = time.time() - start_time
        measured_times.append(elapsed_time)
        print(f"Phase 2. Updated Transform components. Duration: {elapsed_time} seconds.")

        #Phase 3: Adds the Mesh and the Material components to all entities that need it.
        self._BeginBatch()
        start_time = time.time()
        self._AddComponentsToAllEntities()
        azgeneral.idle_wait(1.0)
        self._EndBatch()
        azgeneral.save_level()
        elapsed_time = time.time() - start_time
        measured_times.append(elapsed_time)
        print(f"Phase 3. Added components. Duration: {elapsed_time} seconds.")

        # Phase 4: Sets the mesh asset to all entities with Mesh component. Waits at least 2 frames after each asset is set.
        self._BeginBatch()
        start_time = time.time()
        self._SetMeshAssetToAllEntities()
        azgeneral.idle_wait(1.0)
        self._EndBatch()
        azgeneral.save_level()
        elapsed_time = time.time() - start_time
        measured_times.append(elapsed_time)
        print(f"Phase 4. Set mesh assets on all Mesh components. Duration: {elapsed_time} seconds.")

        # Phase 5: Sets the material assets to all entities with Material component. Waits at least 2 frames after each asset is set.
        self._BeginBatch()
        start_time = time.time()
        self._SetMaterialAssetToAllEntities()
        azgeneral.idle_wait(1.0)
        self._EndBatch()
        azgeneral.save_level()
        elapsed_time = time.time() - start_time
        measured_times.append(elapsed_time)
        print(f"Phase 5. Set material assets on all Material components. Duration: {elapsed_time} seconds.")

        totalTime = 0.0
        for idx, measured_time in enumerate(measured_times):
            totalTime += measured_time
            print(f"PHASE[{idx+1}]. Duration={measured_time} seconds.")
        print(f"Total Duration={totalTime} seconds.")


    def _AddEntitiesRecursive(self, parentEntityName: str, parentEditorEntity: EditorEntity, entities: list) -> int:
        """
        Returns the number of new entities that were added.
        """
        newCount = 0
        for entityDictionary in entities:
            name, editorEntity, isNew = self._AddEntity(parentEntityName, parentEditorEntity, entityDictionary)
            newCount += 1 if isNew else 0
            if ("children" in entityDictionary) and (len(entityDictionary["children"]) > 0):
                newCount += self._AddEntitiesRecursive(name, editorEntity, entityDictionary["children"])
        return newCount


    def _AddEntity(self, parentEntityName: str, parentEditorEntity: EditorEntity, entityDictionary: dict) -> tuple[str, EditorEntity, bool]:
        entityName = entityDictionary["name"]
        editorEntityObj, isNew = self._GetOrCreateEntity(parentEditorEntity, entityName)
        self._entitiesByName[entityName] = EntityData(entityName, editorEntityObj, parentEntityName, entityDictionary)
        return entityName, editorEntityObj, isNew


    def _GetOrCreateEntity(self, parentEditorEntity: EditorEntity, entityName: str) -> tuple[EditorEntity, bool]:
        # Check if an entity like that already exists.
        foundEntities = EditorEntity.find_editor_entities([entityName])
        count = len(foundEntities)
        isNew = (count == 0)
        if count > 1:
            raise Exception(f"Found {count} entities with name={entityName}")
        if isNew:
            entityObj = EditorEntity.create_editor_entity(entityName, parentEditorEntity.id)
        else:
            entityObj = foundEntities[0]
        return entityObj, isNew
    

    def _UpdateTransformComponentForAllEntities(self):
        """
        Visits all entities in self._entitiesByName, and updates the transform components.
        Some entities may need a NonUniformScale component too. it will be added here.
        """
        for name, entityData in self._entitiesByName.items():
            transformDictionary = {}
            if "transform" in entityData.sceneGraphData:
                transformDictionary = entityData.sceneGraphData["transform"]
            hasNonUniformScale = self._UpdateEditorEntityTransform(entityData.editorEntity, transformDictionary)
            childrenCount = 0 if "children" not in entityData.sceneGraphData else len(entityData.sceneGraphData["children"])
            if hasNonUniformScale and childrenCount > 0:
                print(f"WARNING! Entity with name '{name}' has NonUniformScale, but it has {childrenCount} children.\nThese cases are not handled well by O3DE!")


    def _UpdateEditorEntityTransform(self, editorEntityObj: EditorEntity, transformDictionary: dict) -> bool:
        """
        Returns True if the entity requires NonUniformScale component,
        otherwise returns False.
        """
        # DumpComponentProperties(editorEntityObj, "TransformComponent")
        if "translate" in transformDictionary:
            t = transformDictionary["translate"]
            translation = azmath.Vector3(t[0], t[1], t[2])
        else:
            translation = azmath.Vector3(0.0, 0.0, 0.0)

        if "rotate" in transformDictionary:
            r = transformDictionary["rotate"]
            quatX = azmath.Quaternion_CreateRotationX(math.radians(r[0]))
            quatY = azmath.Quaternion_CreateRotationY(math.radians(r[1]))
            quatZ = azmath.Quaternion_CreateRotationZ(math.radians(r[2]))
            quaternion = quatZ.MultiplyQuaternion(quatY).MultiplyQuaternion(quatX)
        else:
            quaternion = azmath.Quaternion_CreateIdentity()

        scaleV = azmath.Vector3(1.0, 1.0, 1.0)
        isUniformScale = True
        if "scale" in transformDictionary:
            s = transformDictionary["scale"]
            scaleV = azmath.Vector3(s[0], s[1], s[2])
            uniformScaleV = azmath.Vector3(s[0], s[0], s[0])
            isUniformScale = scaleV.IsClose(uniformScaleV, 0.01)

        localTM = azmath.Transform_CreateFromQuaternionAndTranslation(
            quaternion, translation
        )
        if isUniformScale:
            localTM.SetUniformScale(scaleV.x)
        else:
            self._AddNonUniformScaleComponent(editorEntityObj, scaleV)
        azcomponents.TransformBus(
            azbus.Event, "SetLocalTM", editorEntityObj.id, localTM
        )
        return (not isUniformScale)


    def _AddNonUniformScaleComponent(self, editorEntityObj: EditorEntity, scaleV: azmath.Vector3):
        # REMARK: The "NonUniformScaleComponent" is an unsual component
        # class not easily accesible via Automation with EditorEnity.add_component()
        # or equivalent functions. The only way to add the component via automation
        # is through the global function azeditor.AddNonUniformScaleComponent()
        azeditor.AddNonUniformScaleComponent(editorEntityObj.id, scaleV)


    def _AddComponentsToAllEntities(self):
        """
        Visits all entities in self._entitiesByName, and adds the missing components (Mesh, Material, etc).
        Components that already exist are captured by reference on each object.
        """
        for name, entityData in self._entitiesByName.items():
            # entityData.sceneGraphData
            # entityData.editorEntity
            if "mesh" not in entityData.sceneGraphData:
                if VERBOSE:
                    print(f"Entity with name '{name}' doesn't need a Mesh component")
                continue
            entityData.meshComponent, wasAdded = self._AddOrGetComponent(entityData.editorEntity, CN_MESH)
            if wasAdded:
                # Let's wait one frame.
                azgeneral.idle_wait_frames(1)
                if VERBOSE:
                    print(f"Added '{CN_MESH}' component to entity named '{name}'")
            if "materials" not in entityData.sceneGraphData:
                # As a warning, because an entity with a Mesh almost always requires a Material component.
                print("WARNING: Entity with name '{}' doesn't need a Material component")
                continue
            entityData.materialComponent, wasAdded = self._AddOrGetComponent(entityData.editorEntity, CN_MATERIAL)
            if wasAdded:
                # Let's wait one frame.
                azgeneral.idle_wait_frames(1)
                if VERBOSE:
                    print(f"Added '{CN_MATERIAL}' component to entity named '{name}'")


    def _AddOrGetComponent(self, editorEntityObj: EditorEntity, componentName: str) -> tuple[EditorComponent, bool]:
        wasAdded = True
        if not editorEntityObj.has_component(componentName):
            component = editorEntityObj.add_component(componentName)
        else:
            wasAdded = False
            componentList = editorEntityObj.get_components_of_type( [componentName,] )
            component = componentList[0]
        return component, wasAdded


    def _SetMeshAssetToAllEntities(self):
        for name, entityData in self._entitiesByName.items():
            # entityData.sceneGraphData
            # entityData.editorEntity
            # entityData.meshComponent
            if entityData.meshComponent is None:
                if VERBOSE:
                    print(f"Entity with name '{name}' doesn't have a Mesh Component.")
                continue
            meshName = entityData.sceneGraphData["mesh"]
            assetProductPath = self._assetPaths.GetMeshAssetProductPath(meshName)
            if self._SetComponentAssetProperty(entityData.meshComponent, "Controller|Configuration|Model Asset", assetProductPath):
                if VERBOSE:
                    print(f"Entity with name '{name}' got its mesh asset updated to '{assetProductPath}'")
                azgeneral.idle_wait_frames(1)


    def _SetComponentAssetProperty(
        self, component: EditorComponent, propertyPath: str, productAssetPath: str
    ) -> bool:
        """
        A generic function that properly sets a component property that accepts an asset.
        For example:
        1. A PhysX Mesh Collider component accepts: Shape Configuration|Asset|PhysX Mesh: ('Asset<MeshAsset>', 'Visible')
        2. A Mesh component accepts: Controller|Configuration|Model Asset: ('Asset<ModelAsset>', 'Visible')
        Returns True if the AssetId was updated in the component. 
        """
        assetId = azasset.AssetCatalogRequestBus(
            azbus.Broadcast, "GetAssetIdByPath", productAssetPath, azmath.Uuid(), False
        )
        if VERBOSE:
            print(f"Got assetId='{assetId}' for '{productAssetPath}'")
        if not assetId.is_valid():
            print(
                f"Skipping property '{propertyPath}' because the asset at '{productAssetPath}' is invalid"
            )
            return False
        # When a Component has been recently created, it takes a while for the properties to show up
        # in the DPE (Document Property Editor), We need to wait and check until the property exists before
        # setting its value.
        frameCountWaitInterval = (
            1  # It's been found that most of the time only one frame is needed to wait.
        )
        timeoutInSeconds = 0.1  # But overall, we are willing to wait up to 0.1 seconds.
        if not WaitUntilTrue(
            lambda: component.check_component_property_value(propertyPath)[0],
            timeoutInSeconds,
            frameCountWaitInterval,
        ):
            print(
                f"ERROR: Component Property '{propertyPath}' never activated after waiting '{timeoutInSeconds}' seconds at '{frameCountWaitInterval}' frames interval."
            )
            return False
        currentAssetId = component.get_component_property_value(propertyPath)
        if currentAssetId.is_valid():
            if currentAssetId.is_equal(assetId):
                if VERBOSE:
                    print(f"Component Property '{propertyPath}' already had its asset set to '{productAssetPath}'('{assetId}')")
                return False
        component.set_component_property_value(propertyPath, assetId)
        return True


    def _SetMaterialAssetToAllEntities(self):
        for name, entityData in self._entitiesByName.items():
            # entityData.sceneGraphData
            # entityData.editorEntity
            # entityData.materialComponent
            if entityData.materialComponent is None:
                if VERBOSE:
                    print(f"Entity with name '{name}' doesn't have a Material Component.")
                continue
            materialList = entityData.sceneGraphData["materials"]
            materialChangedCount = 0
            for slotIndex, materialName in enumerate(materialList):
                materialChangedCount += self._SetMaterialSlotAsset(entityData.materialComponent, materialName, len(materialList))
            if materialChangedCount > 0:
                if VERBOSE:
                    print(f"Entity with name '{name}' got {materialChangedCount} material slots updated")
                azgeneral.idle_wait_frames(3 * materialChangedCount)

    
    def _FindMaterialSlotIndexFromMaterialSlotLabel(self, materialComponent: EditorComponent, materialName: str, maxMaterialSlots: int) -> int:
        entityId = materialComponent.id.get_entity_id()
        noLod = ctypes.c_uint(-1)
        matAssignmentId = azrender.MaterialComponentRequestBus(azbus.Event, "FindMaterialAssignmentId", entityId, noLod.value, materialName)
        slotIndex = 0
        while slotIndex < maxMaterialSlots:
            propertyPath = f"Model Materials|[{slotIndex}]|Material Slot Stable Id"
            try:
                materialSlotStableId = materialComponent.get_component_property_value(propertyPath)
                if materialSlotStableId == matAssignmentId.materialSlotStableId:
                    return slotIndex
            except:
                pass
            slotIndex += 1
        print(f"Failed to find material slot index for entity={entityId}, material slot label={materialName}")
        return -1 # Not found


    def _SetMaterialSlotAsset(self, materialComponent: EditorComponent, materialName: str, maxMaterialSlots: int) -> bool:
        """
        Returns True if the assetId in the given slot was updated.
        """
        materialSlotIndex = self._FindMaterialSlotIndexFromMaterialSlotLabel(materialComponent, materialName, maxMaterialSlots)
        if materialSlotIndex < 0:
            return False
        azmaterialPath = self._assetPaths.GetMaterialAssetProductPath(materialName)
        propertyPath = f"Model Materials|[{materialSlotIndex}]|Material Asset"
        return self._SetComponentAssetProperty(
            materialComponent, propertyPath, azmaterialPath
        )


# pyRunFile C:\GIT\o3dimport\Editor\Scripts\o3dimport\o3dimport.py <Scene Name>
def Main():
    parser = argparse.ArgumentParser(
        description="Automatically Adds entities and componentes from a SceneGraph file and asset layout as produced by O3DEXPORT."
    )
    parser.add_argument("SCENE_NAME", help="Name of the scene to import")
    
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0.1')

    parser.add_argument(
        "--noverbose",
        action="store_true",
        default=False,
        help="Prints detailed progress messages.",
    )

    parser.add_argument(
        "-s",
        "--save_rate",
        type=int,
        default=0,
        help="Save rate. Will save the level for each batch of N entities added.",
    )
    args = parser.parse_args()

    assetPathsObj = AssetPaths(args.SCENE_NAME)
    sceneGraphFilePath = assetPathsObj.GetSceneGraphAbsolutePath()
    global VERBOSE
    VERBOSE = not args.noverbose
    saveRate = args.save_rate
    if not os.path.exists(sceneGraphFilePath):
        print(f"File '{sceneGraphFilePath}' doesn't exist!")
        return
    try:
        with open(sceneGraphFilePath) as f:
            sceneDictionary = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to parse SceneGraph file '{sceneGraphFilePath}'.\n{e}")
        return
    importer = SceneImporter(assetPathsObj, saveRate, sceneDictionary)
    importer.ImportScene()
    # azgeneral.idle_wait(3.0)
    # importer.ImportScene()


if __name__ == "__main__":
    Main()
