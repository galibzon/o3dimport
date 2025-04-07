# Properties of Mesh Component
```
    Info: Controller|Configuration|Lighting Channels|Lighting Channels|Lighting Channel 2 (bool,Visible)
    Info: Controller|Configuration|Lighting Channels|Lighting Channels|Lighting Channel 0 (bool,Visible)
    Info: Model Stats|Mesh Stats|LOD 0 (EditorMeshStatsForLod,Visible)
    Info: Controller|Configuration|Lighting Channels|Lighting Channels|Lighting Channel 4 (bool,Visible)
    Info: Controller|Configuration|Lighting Channels|Lighting Channels|Lighting Channel 3 (bool,Visible)
    Info: Controller|Configuration|Lighting Channels|Lighting Channels (AZStd::array<bool, 5>,Visible)
    Info: Controller|Configuration|Lighting Channels|Lighting Channels|Lighting Channel 1 (bool,Visible)
    Info: Model Stats|Mesh Stats (AZStd::vector<EditorMeshStatsForLod, allocator>,Visible)
    Controller|Configuration|Mesh Asset: ('Asset<ModelAsset>', 'Visible')
    Controller|Configuration|Lod Configuration|Minimum Screen Coverage: ('float', 'NotVisible')
    Controller|Configuration|Lod Configuration|Quality Decay Rate: ('float', 'NotVisible')
    Model Stats: ('EditorMeshStats', 'Visible')
    |Mesh Count: ('unsigned int', 'Visible')
    Controller: ('AZ::Render::MeshComponentController', 'ShowChildrenOnly')
    Controller|Configuration: ('AZ::Render::MeshComponentConfig', 'ShowChildrenOnly')
    Controller|Configuration|Sort Key: ('AZ::s64', 'Visible')
    Controller|Configuration|Support ray intersection: ('bool', 'Visible')
    Controller|Configuration|Model Asset: ('Asset<ModelAsset>', 'Visible')
    Controller|Configuration|Always Moving: ('bool', 'Visible')
    |Vert Count: ('unsigned int', 'Visible')
    Controller|Configuration|Use ray tracing: ('bool', 'Visible')
    Controller|Configuration|Lod Type: ('unsigned char', 'Visible')
    Controller|Configuration|Lod Configuration|Lod Override: ('unsigned char', 'NotVisible')
    |Tri Count: ('unsigned int', 'Visible')
    Controller|Configuration|Exclude from reflection cubemaps: ('bool', 'Visible')
    Controller|Configuration|Visibility: ('bool', 'Visible')
    Controller|Configuration|Use Forward Pass IBL Specular: ('bool', 'Visible')
    Controller|Configuration|Lighting Channels: ('LightingChannelConfiguration', 'ShowChildrenOnly')
```

# Properties of Materia Component
```
Info: Controller|Materials (AZStd::unordered_map<AZ::Render::MaterialAssignmentId, AZ::Render::MaterialAssignment, AZStd::hash<AZ::Render::MaterialAssignmentId>, AZStd::equal_to<AZ::Render::MaterialAssignmentId>, allocator>,Visible)

Info: Controller|Materials|[0] (AZStd::pair<AZ::Render::MaterialAssignmentId, AZ::Render::MaterialAssignment>,Visible)
Info: Controller|Materials|[0]|Key<AZ::Render::MaterialAssignmentId> (AZ::Render::MaterialAssignmentId,Visible)
Info: Controller|Materials|[0]|Value<AZ::Render::MaterialAssignment> (AZ::Render::MaterialAssignment,Visible)
Info: Controller|Materials|[0]|Value<AZ::Render::MaterialAssignment>|Property Overrides (AZStd::unordered_map<Name, AZStd::any, AZStd::hash<Name>, AZStd::equal_to<Name>, allocator>,Visible)




Info: Controller|Materials|[1] (AZStd::pair<AZ::Render::MaterialAssignmentId, AZ::Render::MaterialAssignment>,Visible)
Info: Controller|Materials|[1]|Value<AZ::Render::MaterialAssignment>|Property Overrides (AZStd::unordered_map<Name, AZStd::any, AZStd::hash<Name>, AZStd::equal_to<Name>, allocator>,Visible)
Info: Controller|Materials|[1]|Value<AZ::Render::MaterialAssignment> (AZ::Render::MaterialAssignment,Visible)
Info: Controller|Materials|[1]|Key<AZ::Render::MaterialAssignmentId> (AZ::Render::MaterialAssignmentId,Visible)


Info: Controller|Materials|[2] (AZStd::pair<AZ::Render::MaterialAssignmentId, AZ::Render::MaterialAssignment>,Visible)
Info: Controller|Materials|[2]|Value<AZ::Render::MaterialAssignment>|Property Overrides (AZStd::unordered_map<Name, AZStd::any, AZStd::hash<Name>, AZStd::equal_to<Name>, allocator>,Visible)
Info: Controller|Materials|[2]|Value<AZ::Render::MaterialAssignment> (AZ::Render::MaterialAssignment,Visible)
Info: Controller|Materials|[2]|Key<AZ::Render::MaterialAssignmentId> (AZ::Render::MaterialAssignmentId,Visible)

Info: Model Materials (AZStd::vector<EditorMaterialComponentSlot, allocator>,Visible)




Info: LOD Materials (AZStd::vector<AZStd::vector<EditorMaterialComponentSlot, allocator>, allocator>,NotVisible)
Info: LOD Materials|LOD 0 (AZStd::vector<EditorMaterialComponentSlot, allocator>,Visible)


|Material Asset: ('Asset<MaterialAsset>', 'Visible')

]|Material Asset: ('Asset<MaterialAsset>', 'Visible')

]|LOD Index: ('AZ::u64', 'Visible')

]: ('EditorMaterialComponentSlot', 'ShowChildrenOnly')

Default Material|Material Slot Stable Id: ('unsigned int', 'Visible')

Default Material: ('EditorMaterialComponentSlot', 'ShowChildrenOnly')

Default Material|Material Asset: ('Asset<MaterialAsset>', 'Visible')

Default Material|LOD Index: ('AZ::u64', 'Visible')

]|Material Slot Stable Id: ('unsigned int', 'Visible')

|Material Slot Stable Id: ('unsigned int', 'Visible')

Controller: ('MaterialComponentController', 'ShowChildrenOnly')

|LOD Index: ('AZ::u64', 'Visible')

Enable LOD Materials: ('bool', 'Visible')
```
